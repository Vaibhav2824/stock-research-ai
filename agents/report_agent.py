"""
TradeMind — Report Agent
Compiles all agent outputs into a professional equity research report.
System prompt from the TradeMind plan (Section 5).
"""

import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger("trademind.agents.report")

REPORT_SYSTEM_PROMPT = """You are a senior equity research analyst at Goldman Sachs writing a client-facing report.
Your job is to compile all research data into a professional, evidence-based equity research report.

Return ONLY valid JSON with this schema:
{
    "executive_summary": "<3-4 sentence executive summary>",
    "investment_rating": "BUY" | "HOLD" | "SELL",
    "confidence_level": <integer 0-100>,
    "price_target": <float or null>,
    "price_target_rationale": "<1-2 sentences explaining price target>",
    "sections": {
        "news_and_sentiment": "<2-3 paragraph analysis of news landscape and market sentiment>",
        "technical_analysis": "<2-3 paragraph technical analysis with specific indicator values and interpretation>",
        "fundamental_analysis": "<2-3 paragraph fundamental analysis covering revenue, margins, debt, and guidance>",
        "risk_factors": "<2-3 paragraph risk assessment covering key risks, contradictions, and downside scenarios>",
        "investment_thesis": {
            "bull_case": "<paragraph describing the bull case>",
            "bear_case": "<paragraph describing the bear case>"
        }
    },
    "key_metrics": {
        "sentiment_score": <int or null>,
        "technical_signal": "<string>",
        "fundamental_score": <int or null>,
        "risk_level": "<string>",
        "volatility": "<string>"
    },
    "disclaimer": "This report is for informational purposes only and does not constitute investment advice. Past performance is not indicative of future results."
}

Rules:
- Write in a professional, precise tone suitable for institutional investors
- Cite specific data points: RSI values, sentiment scores, revenue figures, etc.
- Do NOT hallucinate any figures — use only what is provided in the research data
- If data is missing for a section, state that clearly and adjust confidence accordingly
- The investment rating must be supported by the evidence across all sections
- Be balanced — present both bull and bear cases regardless of your rating"""


class ReportAgent(BaseAgent):
    """Compiles all research into a professional equity research report."""

    def __init__(self):
        super().__init__("report_agent", "Senior Equity Research Analyst")

    def run(self, ticker: str, context: dict) -> dict:
        """
        Compile all agent outputs into final report.

        Args:
            ticker: Stock symbol
            context: Full shared context with all agent outputs

        Returns:
            Dict with structured report
        """
        self.logger.info(f"📝 Report Agent starting for {ticker}")

        # Build comprehensive research context
        research_data = self._build_full_context(ticker, context)

        # LLM report generation
        prompt = f"""Using all the research data below, compile a professional equity research report for {ticker}.

{research_data}

Generate the report as JSON following the schema in your instructions."""

        result = self.call_llm_json(prompt, REPORT_SYSTEM_PROMPT, temperature=0.3)

        # Add metadata
        result["status"] = "success"
        result["ticker"] = ticker
        result["company_name"] = context.get("company_info", {}).get("name", ticker)

        self.logger.info(
            f"📝 Report Agent done: rating={result.get('investment_rating', 'N/A')}, "
            f"confidence={result.get('confidence_level', 'N/A')}"
        )
        return result

    def _build_full_context(self, ticker: str, context: dict) -> str:
        """Build the full research context for report generation."""
        parts = []

        # Company info
        company = context.get("company_info", {})
        parts.append(f"=== COMPANY: {company.get('name', ticker)} ({ticker}) ===")
        parts.append(f"Sector: {company.get('sector', 'N/A')}")
        parts.append(f"Industry: {company.get('industry', 'N/A')}")
        parts.append(f"Market Cap: ${company.get('market_cap', 0):,.0f}")
        parts.append(f"Current Price: ${company.get('current_price', 'N/A')}")
        parts.append(f"P/E Ratio: {company.get('pe_ratio', 'N/A')}")
        parts.append(f"52W High: ${company.get('52w_high', 'N/A')}")
        parts.append(f"52W Low: ${company.get('52w_low', 'N/A')}")
        parts.append("")

        # News analysis
        news = context.get("news_analysis", {})
        parts.append("=== NEWS & SENTIMENT ANALYSIS ===")
        if news and news.get("status") not in ("error", None):
            parts.append(f"Overall Sentiment: {news.get('overall_sentiment', 'N/A')}")
            parts.append(f"Sentiment Score: {news.get('sentiment_score', 'N/A')}/100")
            parts.append(f"Key Themes: {', '.join(news.get('key_themes', []))}")
            parts.append(f"Notable Events: {', '.join(news.get('notable_events', []))}")
            parts.append(f"Risk Flags: {', '.join(news.get('risk_flags', []))}")
            parts.append(f"Summary: {news.get('sentiment_summary', 'N/A')}")

            # Include headline analysis
            headlines = news.get("headline_analysis", [])
            if headlines:
                parts.append("Key Headlines:")
                for h in headlines[:5]:
                    parts.append(f"  - [{h.get('sentiment', '')}] {h.get('headline', '')}")
        else:
            parts.append("News data unavailable.")
        parts.append("")

        # Technical analysis
        quant = context.get("quant_analysis", {})
        parts.append("=== TECHNICAL ANALYSIS ===")
        if quant and quant.get("status") not in ("error", None):
            parts.append(f"Trend Signal: {quant.get('trend_signal', 'N/A')}")
            parts.append(f"Confidence: {quant.get('confidence', 'N/A')}/100")
            parts.append(f"Technical Summary: {quant.get('technical_summary', 'N/A')}")

            # Raw indicators
            raw = quant.get("raw_indicators", {})
            if raw:
                rsi = raw.get("rsi", {})
                macd = raw.get("macd", {})
                bb = raw.get("bollinger", {})
                sma = raw.get("sma", {})
                vol = raw.get("volatility", {})

                parts.append(f"RSI(14): {rsi.get('value', 'N/A')} [{rsi.get('signal', '')}]")
                parts.append(f"MACD: {macd.get('macd_line', 'N/A')} vs Signal: {macd.get('signal_line', 'N/A')} [{macd.get('signal', '')}]")
                parts.append(f"Bollinger: Upper=${bb.get('upper', 'N/A')}, Lower=${bb.get('lower', 'N/A')} [{bb.get('signal', '')}]")
                parts.append(f"SMA: 50={sma.get('sma_50', 'N/A')}, 200={sma.get('sma_200', 'N/A')} [{sma.get('golden_cross', '')}]")
                parts.append(f"Volatility: {vol.get('annualized_30d', 'N/A')}% [{vol.get('signal', '')}]")

            # Indicator interpretations
            interp = quant.get("indicator_interpretation", {})
            if interp:
                parts.append("Indicator Interpretations:")
                for key, val in interp.items():
                    parts.append(f"  {key}: {val}")
        else:
            parts.append("Technical data unavailable.")
        parts.append("")

        # Fundamental analysis
        fundamental = context.get("fundamental_analysis", {})
        parts.append("=== FUNDAMENTAL ANALYSIS ===")
        if fundamental and fundamental.get("status") not in ("error", None):
            parts.append(f"Fundamental Score: {fundamental.get('fundamental_score', 'N/A')}/100")
            parts.append(f"Summary: {fundamental.get('fundamental_summary', 'N/A')}")

            for section_key, section_label in [
                ("revenue_growth", "Revenue Growth"),
                ("margins", "Margins"),
                ("debt_and_cash", "Debt & Cash"),
                ("management_guidance", "Management Guidance"),
            ]:
                section = fundamental.get(section_key, {})
                if section:
                    parts.append(f"{section_label}: {section.get('details', section.get('trend', 'N/A'))}")

            risks = fundamental.get("key_risks", [])
            if risks:
                parts.append(f"Key Risks: {', '.join(risks)}")
        else:
            parts.append("Fundamental data unavailable.")
        parts.append("")

        # Risk analysis
        risk = context.get("risk_analysis", {})
        parts.append("=== RISK ASSESSMENT ===")
        if risk and risk.get("status") not in ("error", None):
            parts.append(f"Overall Risk: {risk.get('overall_risk_score', 'N/A')}")
            parts.append(f"Risk Score: {risk.get('risk_score_numeric', 'N/A')}/100")
            parts.append(f"30-day Downside Risk: {risk.get('downside_risk_30d_pct', 'N/A')}%")
            parts.append(f"30-day Upside Potential: {risk.get('upside_potential_30d_pct', 'N/A')}%")
            parts.append(f"Summary: {risk.get('risk_summary', 'N/A')}")

            contradictions = risk.get("signal_contradictions", [])
            if contradictions:
                parts.append("Signal Contradictions:")
                for c in contradictions:
                    parts.append(f"  - {c.get('explanation', '')}")

            bear_cats = risk.get("bear_catalysts", [])
            if bear_cats:
                parts.append("Bear Catalysts:")
                for c in bear_cats:
                    parts.append(f"  - {c.get('catalyst', '')} (Prob: {c.get('probability', '')}, Impact: {c.get('impact', '')})")

            bull_cats = risk.get("bull_catalysts", [])
            if bull_cats:
                parts.append("Bull Catalysts:")
                for c in bull_cats:
                    parts.append(f"  - {c.get('catalyst', '')} (Prob: {c.get('probability', '')}, Impact: {c.get('impact', '')})")
        else:
            parts.append("Risk data unavailable.")

        return "\n".join(parts)
