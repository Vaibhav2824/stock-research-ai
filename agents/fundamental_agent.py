"""
TradeMind — Fundamental Agent (RAG)
Retrieves SEC filings, builds vector index, runs RAG queries for fundamental analysis.
System prompt from the TradeMind plan (Section 5).
"""

import logging
from agents.base_agent import BaseAgent
from tools.edgar_tool import download_filing
from tools.yfinance_tool import get_financials
from rag.indexer import build_index
from rag.retriever import multi_query_retrieve

logger = logging.getLogger("trademind.agents.fundamental")

FUNDAMENTAL_SYSTEM_PROMPT = """You are a fundamental equity analyst at a top-tier investment bank.
Your job is to analyze SEC filing excerpts and financial data to assess the company's fundamentals.

Based on the provided context, return ONLY valid JSON with this schema:
{
    "revenue_growth": {
        "trend": "Growing" | "Declining" | "Stable",
        "details": "<2-3 sentence analysis with specific numbers if available>",
        "yoy_growth_pct": <float or null>
    },
    "margins": {
        "gross_margin_trend": "Expanding" | "Contracting" | "Stable",
        "operating_margin_trend": "Expanding" | "Contracting" | "Stable",
        "details": "<2-3 sentence analysis>"
    },
    "debt_and_cash": {
        "debt_to_equity": <float or null>,
        "cash_position": "<description of cash/liquidity>",
        "risk_level": "Low" | "Medium" | "High",
        "details": "<2-3 sentence analysis>"
    },
    "management_guidance": {
        "outlook": "Positive" | "Cautious" | "Negative" | "Not Available",
        "key_points": ["point1", "point2"],
        "details": "<2-3 sentence analysis>"
    },
    "key_risks": ["risk1", "risk2", "risk3"],
    "fundamental_score": <integer 0-100, where 100=strongest fundamentals>,
    "fundamental_summary": "<3-4 sentence overall fundamental assessment>"
}

Rules:
- Base your analysis ONLY on the provided filing excerpts and financial data
- Cite specific numbers when available
- If data is insufficient for a field, set it to null or "Not Available"
- Do NOT hallucinate financial figures
- Focus on forward-looking indicators where available"""


class FundamentalAgent(BaseAgent):
    """Analyzes SEC filings using RAG to extract fundamental insights."""

    def __init__(self):
        super().__init__("fundamental_agent", "Fundamental Equity Analyst")

    def run(self, ticker: str, context: dict) -> dict:
        """
        Download SEC filing, build RAG index, run queries, and analyze.

        Args:
            ticker: Stock symbol
            context: Shared context

        Returns:
            Dict with fundamental analysis
        """
        self.logger.info(f"📑 Fundamental Agent starting for {ticker}")

        # Step 1: Get filing text
        filing_text = self._get_filing_text(ticker)

        # Step 2: Get yfinance financials as supplementary data
        financials = get_financials(ticker)
        financials_summary = self._format_financials(financials)

        # Step 3: RAG if we have filing text
        rag_context = ""
        if filing_text:
            rag_context = self._run_rag_queries(filing_text, ticker)

        # Step 4: LLM analysis
        prompt = self._build_prompt(ticker, rag_context, financials_summary)
        result = self.call_llm_json(prompt, FUNDAMENTAL_SYSTEM_PROMPT)

        # Add metadata
        result["status"] = "success"
        result["data_sources"] = []
        if filing_text:
            result["data_sources"].append("SEC 10-K Filing")
        if financials_summary:
            result["data_sources"].append("yfinance Financial Statements")
        if not filing_text and not financials_summary:
            result["status"] = "partial"
            result["data_sources"].append("Limited data available")

        self.logger.info(
            f"📑 Fundamental Agent done: score={result.get('fundamental_score', 'N/A')}"
        )
        return result

    def _get_filing_text(self, ticker: str) -> str:
        """Try to download SEC filing. Returns empty string on failure."""
        # Try 10-K first, then 10-Q
        for filing_type in ["10-K", "10-Q"]:
            self.logger.info(f"Attempting to download {filing_type} for {ticker}...")
            text = download_filing(ticker, filing_type=filing_type)
            if text and len(text) > 500:
                self.logger.info(f"Got {filing_type} filing: {len(text)} chars")
                return text

        self.logger.warning(f"No SEC filing available for {ticker}")
        return ""

    def _run_rag_queries(self, filing_text: str, ticker: str) -> str:
        """Build vector index and run RAG queries."""
        self.logger.info(f"Building FAISS index for {ticker}...")

        # Build index
        index, chunks = build_index(filing_text, ticker)
        if index is None:
            return ""

        # Run key queries
        queries = [
            "revenue growth trend and total revenue",
            "gross margin and operating margin",
            "total debt, debt-to-equity ratio, and cash position",
            "management forward guidance and outlook",
            "key risk factors and material risks",
        ]

        retrieved_chunks = multi_query_retrieve(queries, ticker, top_k=3)

        if not retrieved_chunks:
            return ""

        # Format as RAG context
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks[:15], 1):  # Cap at 15 chunks
            context_parts.append(f"[Filing Excerpt {i}]\n{chunk[:800]}")

        return "\n\n".join(context_parts)

    def _format_financials(self, financials: dict) -> str:
        """Format yfinance financials into readable text."""
        if not financials or "error" in financials:
            return ""

        parts = []

        # Revenue
        revenue = financials.get("revenue", [])
        if revenue:
            parts.append("Revenue (Recent Years):")
            for item in revenue[:4]:
                if item.get("value"):
                    parts.append(f"  {item['date']}: ${item['value']:,.0f}")

        # Net Income
        net_income = financials.get("net_income", [])
        if net_income:
            parts.append("Net Income (Recent Years):")
            for item in net_income[:4]:
                if item.get("value"):
                    parts.append(f"  {item['date']}: ${item['value']:,.0f}")

        # Debt
        debt = financials.get("total_debt", [])
        if debt:
            parts.append("Total Debt (Recent):")
            for item in debt[:2]:
                if item.get("value"):
                    parts.append(f"  {item['date']}: ${item['value']:,.0f}")

        # Cash
        cash = financials.get("cash", [])
        if cash:
            parts.append("Cash & Equivalents (Recent):")
            for item in cash[:2]:
                if item.get("value"):
                    parts.append(f"  {item['date']}: ${item['value']:,.0f}")

        return "\n".join(parts) if parts else ""

    def _build_prompt(self, ticker: str, rag_context: str, financials_summary: str) -> str:
        """Build the full prompt for fundamental analysis."""
        prompt_parts = [f"Analyze the fundamentals of {ticker} based on the following data:\n"]

        if rag_context:
            prompt_parts.append("=== SEC FILING EXCERPTS (Retrieved via RAG) ===")
            prompt_parts.append(rag_context)
            prompt_parts.append("")

        if financials_summary:
            prompt_parts.append("=== FINANCIAL STATEMENTS (from yfinance) ===")
            prompt_parts.append(financials_summary)
            prompt_parts.append("")

        if not rag_context and not financials_summary:
            prompt_parts.append(
                "Note: Limited financial data is available. Provide analysis based on "
                "general knowledge of this company, but clearly state that data is limited."
            )

        prompt_parts.append(
            "\nProvide your fundamental analysis as JSON following the schema in your instructions."
        )
        return "\n".join(prompt_parts)
