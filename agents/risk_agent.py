"""
TradeMind — Risk Agent
Synthesises all prior agent outputs to produce a holistic risk assessment.
System prompt from the TradeMind plan (Section 5).
"""

import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger("trademind.agents.risk")

RISK_SYSTEM_PROMPT = """You are a senior risk analyst at a top hedge fund.
Your job is to review all research data produced by other analysts and create a holistic risk assessment.

You must identify contradictions between signals, assess overall risk, and provide actionable risk intelligence.

Return ONLY valid JSON with this schema:
{
    "overall_risk_score": "Low" | "Medium" | "High" | "Critical",
    "risk_score_numeric": <integer 0-100, where 100=highest risk>,
    "signal_contradictions": [
        {"signals": ["signal1", "signal2"], "explanation": "<why they contradict>"}
    ],
    "bear_catalysts": [
        {"catalyst": "<description>", "probability": "High" | "Medium" | "Low", "impact": "High" | "Medium" | "Low"}
    ],
    "bull_catalysts": [
        {"catalyst": "<description>", "probability": "High" | "Medium" | "Low", "impact": "High" | "Medium" | "Low"}
    ],
    "downside_risk_30d_pct": <float, estimated percentage>,
    "upside_potential_30d_pct": <float, estimated percentage>,
    "key_risk_factors": ["risk1", "risk2", "risk3"],
    "risk_summary": "<3-4 sentence overall risk assessment>",
    "recommendation_modifier": "<how risk assessment should modify the investment thesis>"
}

Rules:
- Cross-reference news sentiment, technical signals, and fundamental data
- Flag ANY contradictions (e.g., bullish technicals but negative news)
- Be conservative in risk estimation — better to over-warn than under-warn
- If any agent data is missing, flag that explicitly as a risk factor
- Cite specific data points from the research to support your assessment"""


class RiskAgent(BaseAgent):
    """Synthesises all agent outputs into a comprehensive risk assessment."""

    def __init__(self):
        super().__init__("risk_agent", "Senior Risk Analyst")

    def run(self, ticker: str, context: dict) -> dict:
        """
        Analyze all prior agent outputs and produce risk assessment.

        Args:
            ticker: Stock symbol
            context: Shared context with outputs from News, Quant, and Fundamental agents

        Returns:
            Dict with risk assessment
        """
        self.logger.info(f"⚠️  Risk Agent starting for {ticker}")

        # Gather all prior agent outputs
        research_summary = self._build_research_summary(ticker, context)

        # LLM risk analysis
        prompt = f"""Review the following research data for {ticker} and produce a comprehensive risk assessment:

{research_summary}

Provide your risk analysis as JSON following the schema in your instructions."""

        result = self.call_llm_json(prompt, RISK_SYSTEM_PROMPT)

        # Add metadata
        result["status"] = "success"
        result["data_completeness"] = self._assess_data_completeness(context)

        self.logger.info(
            f"⚠️  Risk Agent done: risk={result.get('overall_risk_score', 'N/A')}, "
            f"score={result.get('risk_score_numeric', 'N/A')}"
        )
        return result

    def _build_research_summary(self, ticker: str, context: dict) -> str:
        """Build a comprehensive summary of all prior agent outputs."""
        parts = [f"Stock: {ticker}\n"]

        # Company info
        company = context.get("company_info", {})
        if company:
            parts.append(f"Company: {company.get('name', ticker)}")
            parts.append(f"Sector: {company.get('sector', 'N/A')}")
            parts.append(f"Market Cap: ${company.get('market_cap', 0):,.0f}")
            parts.append(f"Current Price: ${company.get('current_price', 'N/A')}")
            parts.append("")

        # News sentiment
        news = context.get("news_analysis", {})
        if news and news.get("status") != "error":
            parts.append("=== NEWS SENTIMENT ===")
            parts.append(f"Overall Sentiment: {news.get('overall_sentiment', 'N/A')}")
            parts.append(f"Sentiment Score: {news.get('sentiment_score', 'N/A')}/100")
            parts.append(f"Key Themes: {', '.join(news.get('key_themes', []))}")
            parts.append(f"Risk Flags: {', '.join(news.get('risk_flags', []))}")
            parts.append(f"Summary: {news.get('sentiment_summary', 'N/A')}")
            parts.append("")
        else:
            parts.append("=== NEWS SENTIMENT === (Data unavailable)\n")

        # Technical analysis
        quant = context.get("quant_analysis", {})
        if quant and quant.get("status") != "error":
            parts.append("=== TECHNICAL ANALYSIS ===")
            parts.append(f"Trend Signal: {quant.get('trend_signal', 'N/A')}")
            parts.append(f"Confidence: {quant.get('confidence', 'N/A')}/100")
            parts.append(f"Summary: {quant.get('technical_summary', 'N/A')}")

            raw = quant.get("raw_indicators", {})
            if raw:
                parts.append(f"RSI: {raw.get('rsi', {}).get('value', 'N/A')}")
                parts.append(f"MACD Signal: {raw.get('macd', {}).get('signal', 'N/A')}")
                parts.append(f"Volatility: {raw.get('volatility', {}).get('annualized_30d', 'N/A')}%")
            parts.append("")
        else:
            parts.append("=== TECHNICAL ANALYSIS === (Data unavailable)\n")

        # Fundamental analysis
        fundamental = context.get("fundamental_analysis", {})
        if fundamental and fundamental.get("status") != "error":
            parts.append("=== FUNDAMENTAL ANALYSIS ===")
            parts.append(f"Fundamental Score: {fundamental.get('fundamental_score', 'N/A')}/100")
            parts.append(f"Summary: {fundamental.get('fundamental_summary', 'N/A')}")

            revenue = fundamental.get("revenue_growth", {})
            if revenue:
                parts.append(f"Revenue Trend: {revenue.get('trend', 'N/A')}")
            debt = fundamental.get("debt_and_cash", {})
            if debt:
                parts.append(f"Debt Risk: {debt.get('risk_level', 'N/A')}")
            parts.append(f"Key Risks: {', '.join(fundamental.get('key_risks', []))}")
            parts.append("")
        else:
            parts.append("=== FUNDAMENTAL ANALYSIS === (Data unavailable)\n")

        return "\n".join(parts)

    def _assess_data_completeness(self, context: dict) -> dict:
        """Assess how complete the research data is."""
        completeness = {}
        for key, label in [
            ("news_analysis", "News"),
            ("quant_analysis", "Technical"),
            ("fundamental_analysis", "Fundamental"),
        ]:
            data = context.get(key, {})
            if not data:
                completeness[label] = "Missing"
            elif data.get("status") == "error":
                completeness[label] = "Error"
            elif data.get("status") == "no_data":
                completeness[label] = "No Data"
            else:
                completeness[label] = "Complete"
        return completeness
