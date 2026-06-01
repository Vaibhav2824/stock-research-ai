"""
TradeMind — News Agent
Scrapes and analyses recent financial news, press releases, and sentiment.
System prompt from the TradeMind plan (Section 5).
"""

import logging
from agents.base_agent import BaseAgent
from tools.news_tool import fetch_news

logger = logging.getLogger("trademind.agents.news")

NEWS_SYSTEM_PROMPT = """You are a financial news analyst at a top equity research firm.
Your job is to analyze recent news articles about a stock and produce a structured sentiment analysis.

You must return ONLY valid JSON with this exact schema:
{
    "overall_sentiment": "Bullish" | "Bearish" | "Neutral",
    "sentiment_score": <integer 0-100, where 0=most bearish, 50=neutral, 100=most bullish>,
    "key_themes": ["theme1", "theme2", "theme3"],
    "notable_events": ["event1", "event2"],
    "risk_flags": ["risk1", "risk2"],
    "sentiment_summary": "<2-3 sentence summary of the news landscape>",
    "headline_analysis": [
        {"headline": "...", "sentiment": "Positive" | "Negative" | "Neutral", "impact": "High" | "Medium" | "Low"}
    ]
}

Rules:
- Analyze sentiment objectively based on the actual news content
- Consider both positive and negative signals
- Flag any earnings surprises, lawsuits, partnerships, or regulatory actions
- Do NOT hallucinate events that aren't in the provided news
- If news is limited, say so in the summary"""


class NewsAgent(BaseAgent):
    """Scrapes and analyses recent financial news for a stock."""

    def __init__(self):
        super().__init__("news_agent", "Financial News Analyst")

    def run(self, ticker: str, context: dict) -> dict:
        """
        Fetch news and analyze sentiment.

        Args:
            ticker: Stock symbol
            context: Shared context (may contain company_name from prior tools)

        Returns:
            Dict with sentiment analysis
        """
        self.logger.info(f"🗞️  News Agent starting for {ticker}")

        # Get company name from context if available
        company_name = context.get("company_info", {}).get("name", "")

        # Fetch news articles
        articles = fetch_news(ticker, company_name=company_name, days=14)

        if not articles:
            self.logger.warning(f"No news found for {ticker}")
            return {
                "status": "no_data",
                "overall_sentiment": "Neutral",
                "sentiment_score": 50,
                "key_themes": [],
                "notable_events": [],
                "risk_flags": [],
                "sentiment_summary": f"No recent news articles found for {ticker}.",
                "headline_analysis": [],
                "articles_analyzed": 0,
            }

        # Format articles for LLM
        articles_text = self._format_articles(articles)

        # LLM analysis
        prompt = f"""Analyze the following recent news articles for {ticker} ({company_name}):

{articles_text}

Provide your analysis as a JSON object following the schema specified in your instructions."""

        result = self.call_llm_json(prompt, NEWS_SYSTEM_PROMPT)

        # Add metadata
        result["status"] = "success"
        result["articles_analyzed"] = len(articles)
        result["articles"] = articles[:10]  # Keep top 10 for reference

        self.logger.info(
            f"🗞️  News Agent done: sentiment={result.get('overall_sentiment', 'N/A')}, "
            f"score={result.get('sentiment_score', 'N/A')}"
        )
        return result

    def _format_articles(self, articles: list[dict]) -> str:
        """Format articles into a readable text block for the LLM."""
        lines = []
        for i, article in enumerate(articles[:15], 1):  # Cap at 15
            lines.append(f"Article {i}:")
            lines.append(f"  Title: {article.get('title', 'N/A')}")
            lines.append(f"  Source: {article.get('source', 'N/A')}")
            lines.append(f"  Date: {article.get('published_at', 'N/A')}")
            desc = article.get("description", "")
            if desc:
                lines.append(f"  Summary: {desc[:300]}")
            lines.append("")
        return "\n".join(lines)
