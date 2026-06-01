"""
TradeMind — Quant Agent
Computes technical indicators and generates a trend signal.
System prompt from the TradeMind plan (Section 5).
"""

import logging
from agents.base_agent import BaseAgent
from tools.yfinance_tool import get_stock_data
from tools.ta_tool import compute_indicators

logger = logging.getLogger("trademind.agents.quant")

QUANT_SYSTEM_PROMPT = """You are a quantitative analyst at a top hedge fund.
Your job is to interpret technical indicator values and produce a trading signal.

You will be given raw technical indicator data. Analyze it and return ONLY valid JSON:
{
    "trend_signal": "Strong Buy" | "Buy" | "Hold" | "Sell" | "Strong Sell",
    "confidence": <integer 0-100>,
    "support_level": <float>,
    "resistance_level": <float>,
    "technical_summary": "<2-3 sentence technical outlook>",
    "indicator_interpretation": {
        "rsi": "<1 sentence interpretation>",
        "macd": "<1 sentence interpretation>",
        "bollinger": "<1 sentence interpretation>",
        "moving_averages": "<1 sentence interpretation>",
        "volatility": "<1 sentence interpretation>"
    },
    "key_levels": {
        "immediate_support": <float>,
        "immediate_resistance": <float>,
        "strong_support": <float>,
        "strong_resistance": <float>
    }
}

Rules:
- Base your analysis ONLY on the provided indicator values
- Be specific about price levels
- Factor in all indicators for your overall signal
- High RSI (>70) = overbought risk; Low RSI (<30) = oversold opportunity
- MACD crossover above signal line = bullish; below = bearish
- Price near upper Bollinger = potential pullback; near lower = potential bounce"""


class QuantAgent(BaseAgent):
    """Computes technical indicators and generates trend signal."""

    def __init__(self):
        super().__init__("quant_agent", "Quantitative Analyst")

    def run(self, ticker: str, context: dict) -> dict:
        """
        Compute technical indicators and get LLM interpretation.

        Args:
            ticker: Stock symbol
            context: Shared context

        Returns:
            Dict with technical analysis and trend signal
        """
        self.logger.info(f"📊 Quant Agent starting for {ticker}")

        # Fetch OHLCV data
        df = get_stock_data(ticker, period="1y")

        if df.empty:
            self.logger.error(f"No price data for {ticker}")
            return {
                "status": "error",
                "error": f"No price data available for {ticker}",
                "trend_signal": "N/A",
            }

        # Compute all technical indicators
        indicators = compute_indicators(df)

        if "error" in indicators:
            return {
                "status": "error",
                "error": indicators["error"],
                "trend_signal": "N/A",
            }

        # Format indicators for LLM
        indicators_text = self._format_indicators(ticker, indicators)

        # LLM interpretation
        prompt = f"""Here are the current technical indicators for {ticker}:

{indicators_text}

Analyze these indicators and provide your technical analysis as JSON following the schema in your instructions."""

        result = self.call_llm_json(prompt, QUANT_SYSTEM_PROMPT)

        # Merge raw indicators into result
        result["raw_indicators"] = indicators
        result["status"] = "success"

        self.logger.info(
            f"📊 Quant Agent done: signal={result.get('trend_signal', 'N/A')}, "
            f"confidence={result.get('confidence', 'N/A')}"
        )
        return result

    def _format_indicators(self, ticker: str, ind: dict) -> str:
        """Format indicators into readable text for LLM."""
        price = ind.get("price", {})
        rsi = ind.get("rsi", {})
        macd = ind.get("macd", {})
        bb = ind.get("bollinger", {})
        sma = ind.get("sma", {})
        vol = ind.get("volatility", {})

        return f"""Ticker: {ticker}
Current Price: ${price.get('current', 'N/A')}
1-Day Change: {price.get('change_1d', 'N/A')}%
30-Day Change: {price.get('change_30d', 'N/A')}%
30-Day High: ${price.get('high_30d', 'N/A')}
30-Day Low: ${price.get('low_30d', 'N/A')}

RSI (14): {rsi.get('value', 'N/A')} — Signal: {rsi.get('signal', 'N/A')}

MACD Line: {macd.get('macd_line', 'N/A')}
Signal Line: {macd.get('signal_line', 'N/A')}
Histogram: {macd.get('histogram', 'N/A')}
MACD Signal: {macd.get('signal', 'N/A')}

Bollinger Bands:
  Upper: ${bb.get('upper', 'N/A')}
  Middle: ${bb.get('middle', 'N/A')}
  Lower: ${bb.get('lower', 'N/A')}
  Price Position: {bb.get('signal', 'N/A')}

Moving Averages:
  50-SMA: ${sma.get('sma_50', 'N/A')}
  200-SMA: ${sma.get('sma_200', 'N/A')}
  Cross: {sma.get('golden_cross', 'N/A')}

Volatility (30-day annualized): {vol.get('annualized_30d', 'N/A')}%
Volatility Level: {vol.get('signal', 'N/A')}

Overall Computed Signal: {ind.get('overall_signal', 'N/A')}"""
