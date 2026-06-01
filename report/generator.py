"""
TradeMind — Markdown Report Generator
Compiles agent outputs into a professional markdown equity research report.
"""

import logging
from datetime import datetime

logger = logging.getLogger("trademind.report.generator")


def generate_markdown_report(ticker: str, context: dict) -> str:
    """
    Generate a professional markdown equity research report.

    Args:
        ticker: Stock symbol
        context: Full pipeline context with all agent outputs

    Returns:
        Formatted markdown string
    """
    report = context.get("report", {})
    company = context.get("company_info", {})
    news = context.get("news_analysis", {})
    quant = context.get("quant_analysis", {})
    fundamental = context.get("fundamental_analysis", {})
    risk = context.get("risk_analysis", {})

    company_name = company.get("name", ticker)
    rating = report.get("investment_rating", "N/A")
    confidence = report.get("confidence_level", "N/A")
    price_target = report.get("price_target")
    current_price = company.get("current_price", "N/A")

    # Build rating badge
    rating_emoji = {"BUY": "🟢", "HOLD": "🟡", "SELL": "🔴"}.get(rating, "⚪")

    sections = report.get("sections", {})
    key_metrics = report.get("key_metrics", {})

    date_str = datetime.now().strftime("%B %d, %Y")

    md = f"""# 📊 TradeMind Equity Research Report

## {company_name} ({ticker})

**Date:** {date_str}
**Analyst:** TradeMind AI Research Platform

---

## {rating_emoji} Investment Rating: **{rating}**

| Metric | Value |
|--------|-------|
| **Rating** | {rating} |
| **Confidence** | {confidence}/100 |
| **Current Price** | ${current_price} |
| **Price Target** | {"$" + str(price_target) if price_target else "N/A"} |
| **Sector** | {company.get('sector', 'N/A')} |
| **Market Cap** | ${company.get('market_cap', 0):,.0f} |
| **P/E Ratio** | {company.get('pe_ratio', 'N/A')} |

---

## 📋 Executive Summary

{report.get('executive_summary', 'No executive summary available.')}

{f"**Price Target Rationale:** {report.get('price_target_rationale', '')}" if report.get('price_target_rationale') else ""}

---

## 📰 News & Market Sentiment

{sections.get('news_and_sentiment', _fallback_news_section(news))}

**Sentiment Score:** {news.get('sentiment_score', 'N/A')}/100 ({news.get('overall_sentiment', 'N/A')})

---

## 📈 Technical Analysis

{sections.get('technical_analysis', _fallback_technical_section(quant))}

### Key Technical Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI (14) | {_safe_get(quant, 'raw_indicators', 'rsi', 'value', default='N/A')} | {_safe_get(quant, 'raw_indicators', 'rsi', 'signal', default='N/A')} |
| MACD | {_safe_get(quant, 'raw_indicators', 'macd', 'macd_line', default='N/A')} | {_safe_get(quant, 'raw_indicators', 'macd', 'signal', default='N/A')} |
| Bollinger | — | {_safe_get(quant, 'raw_indicators', 'bollinger', 'signal', default='N/A')} |
| 50 SMA | ${_safe_get(quant, 'raw_indicators', 'sma', 'sma_50', default='N/A')} | — |
| 200 SMA | ${_safe_get(quant, 'raw_indicators', 'sma', 'sma_200', default='N/A')} | {_safe_get(quant, 'raw_indicators', 'sma', 'golden_cross', default='N/A')} |
| Volatility | {_safe_get(quant, 'raw_indicators', 'volatility', 'annualized_30d', default='N/A')}% | {_safe_get(quant, 'raw_indicators', 'volatility', 'signal', default='N/A')} |

---

## 📑 Fundamental Analysis

{sections.get('fundamental_analysis', _fallback_fundamental_section(fundamental))}

**Fundamental Score:** {fundamental.get('fundamental_score', 'N/A')}/100

---

## ⚠️ Risk Factors

{sections.get('risk_factors', _fallback_risk_section(risk))}

| Risk Metric | Value |
|-------------|-------|
| **Overall Risk** | {risk.get('overall_risk_score', 'N/A')} |
| **Risk Score** | {risk.get('risk_score_numeric', 'N/A')}/100 |
| **30-Day Downside** | {risk.get('downside_risk_30d_pct', 'N/A')}% |
| **30-Day Upside** | {risk.get('upside_potential_30d_pct', 'N/A')}% |

---

## 💡 Investment Thesis

### Bull Case 🐂
{_safe_get(report, 'sections', 'investment_thesis', 'bull_case', default=report.get('bull_case', _safe_get(risk, 'bull_catalysts', 0, 'catalyst', default='Favorable conditions expected.')))}

### Bear Case 🐻
{_safe_get(report, 'sections', 'investment_thesis', 'bear_case', default=report.get('bear_case', _safe_get(risk, 'bear_catalysts', 0, 'catalyst', default='Potential downside risks remain.')))}

---

## 📊 Key Metrics Summary

| Metric | Value |
|--------|-------|
| Sentiment Score | {key_metrics.get('sentiment_score', news.get('sentiment_score', 'N/A'))}/100 |
| Technical Signal | {key_metrics.get('technical_signal', quant.get('trend_signal', 'N/A'))} |
| Fundamental Score | {key_metrics.get('fundamental_score', fundamental.get('fundamental_score', 'N/A'))}/100 |
| Risk Level | {key_metrics.get('risk_level', risk.get('overall_risk_score', 'N/A'))} |
| Volatility | {key_metrics.get('volatility', _safe_get(quant, 'raw_indicators', 'volatility', 'signal', default='N/A'))} |

---

*{report.get('disclaimer', 'This report is for informational purposes only and does not constitute investment advice.')}*

*Generated by TradeMind AI — {date_str}*
"""

    logger.info(f"Generated markdown report for {ticker}: {len(md)} chars")
    return md


def _safe_get(d: dict, *keys, default="N/A"):
    """Safely navigate nested dicts."""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d if d is not None else default


def _fallback_news_section(news: dict) -> str:
    """Generate fallback news section from raw agent output."""
    if not news or news.get("status") == "error":
        return "News data was unavailable for this analysis."
    return news.get("sentiment_summary", "No news analysis available.")


def _fallback_technical_section(quant: dict) -> str:
    """Generate fallback technical section."""
    if not quant or quant.get("status") == "error":
        return "Technical analysis data was unavailable."
    return quant.get("technical_summary", "No technical analysis available.")


def _fallback_fundamental_section(fundamental: dict) -> str:
    """Generate fallback fundamental section."""
    if not fundamental or fundamental.get("status") == "error":
        return "Fundamental analysis data was unavailable."
    return fundamental.get("fundamental_summary", "No fundamental analysis available.")


def _fallback_risk_section(risk: dict) -> str:
    """Generate fallback risk section."""
    if not risk or risk.get("status") == "error":
        return "Risk assessment data was unavailable."
    return risk.get("risk_summary", "No risk assessment available.")
