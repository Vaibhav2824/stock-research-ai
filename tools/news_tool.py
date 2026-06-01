"""
TradeMind — News Tool
Fetches financial news from NewsAPI (primary) and Yahoo Finance RSS (fallback).
"""

import logging
import os
from datetime import datetime, timedelta
import requests
import feedparser

logger = logging.getLogger("trademind.tools.news")

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSAPI_URL = "https://newsapi.org/v2/everything"


def fetch_news(ticker: str, company_name: str = "", days: int = 14) -> list[dict]:
    """
    Fetch recent financial news for a stock.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        company_name: Full company name for better search
        days: Number of days to look back

    Returns:
        List of dicts: {title, source, url, published_at, description}
    """
    articles = []

    # Try NewsAPI first
    if NEWSAPI_KEY:
        try:
            articles = _fetch_newsapi(ticker, company_name, days)
            if articles:
                logger.info(f"NewsAPI returned {len(articles)} articles for {ticker}")
                return articles[:20]  # Cap at 20
        except Exception as e:
            logger.warning(f"NewsAPI failed for {ticker}: {e}")

    # Fallback to Yahoo Finance RSS
    try:
        articles = _fetch_yahoo_rss(ticker)
        if articles:
            logger.info(f"Yahoo RSS returned {len(articles)} articles for {ticker}")
            return articles[:20]
    except Exception as e:
        logger.warning(f"Yahoo RSS failed for {ticker}: {e}")

    # Fallback to Google News RSS
    try:
        articles = _fetch_google_news_rss(ticker, company_name)
        if articles:
            logger.info(f"Google News RSS returned {len(articles)} articles for {ticker}")
            return articles[:20]
    except Exception as e:
        logger.warning(f"Google News RSS failed for {ticker}: {e}")

    logger.error(f"All news sources failed for {ticker}")
    return []


def _fetch_newsapi(ticker: str, company_name: str, days: int) -> list[dict]:
    """Fetch news from NewsAPI (free tier: 100 requests/day)."""
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Build search query: ticker OR company name
    query = ticker
    if company_name:
        query = f'"{company_name}" OR {ticker}'

    params = {
        "q": query,
        "from": from_date,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": 20,
        "apiKey": NEWSAPI_KEY,
    }

    response = requests.get(NEWSAPI_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "ok":
        raise ValueError(f"NewsAPI error: {data.get('message', 'Unknown error')}")

    articles = []
    for article in data.get("articles", []):
        articles.append({
            "title": article.get("title", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
            "url": article.get("url", ""),
            "published_at": article.get("publishedAt", ""),
            "description": article.get("description", "")[:500],
        })

    return articles


def _fetch_yahoo_rss(ticker: str) -> list[dict]:
    """Fetch news from Yahoo Finance RSS feed (no API key needed)."""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"

    feed = feedparser.parse(url)

    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.get("title", ""),
            "source": "Yahoo Finance",
            "url": entry.get("link", ""),
            "published_at": entry.get("published", ""),
            "description": entry.get("summary", "")[:500],
        })

    return articles


def _fetch_google_news_rss(ticker: str, company_name: str = "") -> list[dict]:
    """Fetch from Google News RSS (no API key needed)."""
    query = f"{ticker} stock" if not company_name else f"{company_name} stock"
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(url)

    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.get("title", ""),
            "source": entry.get("source", {}).get("title", "Google News"),
            "url": entry.get("link", ""),
            "published_at": entry.get("published", ""),
            "description": entry.get("summary", "")[:500],
        })

    return articles
