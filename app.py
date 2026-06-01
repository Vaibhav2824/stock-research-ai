"""
TradeMind — AI-Powered Stock Research Platform
Main Streamlit application.
"""

import streamlit as st
import time
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(__file__))

from config import logger
from orchestrator import run_analysis
from report.generator import generate_markdown_report
from report.pdf_export import export_pdf

# ============================================
# Page Configuration
# ============================================
st.set_page_config(
    page_title="TradeMind AI | Equity Research",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================
# Custom CSS — Premium Dark Theme
# ============================================
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Hero Section */
    .hero-container {
        text-align: center;
        padding: 2rem 1rem;
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3B82F6, #8B5CF6, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        opacity: 0.7;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    /* Status Cards */
    .agent-card {
        padding: 1rem 1.25rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(255,255,255,0.06);
        background: rgba(255,255,255,0.03);
        transition: all 0.3s ease;
    }
    .agent-card:hover {
        border-color: rgba(59, 130, 246, 0.3);
        background: rgba(59, 130, 246, 0.05);
    }
    .agent-card.running {
        border-color: rgba(59, 130, 246, 0.5);
        background: rgba(59, 130, 246, 0.08);
        animation: pulse 2s ease-in-out infinite;
    }
    .agent-card.done {
        border-color: rgba(34, 197, 94, 0.4);
        background: rgba(34, 197, 94, 0.05);
    }
    .agent-card.error {
        border-color: rgba(239, 68, 68, 0.4);
        background: rgba(239, 68, 68, 0.05);
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Rating Badge */
    .rating-badge {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 8px;
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-align: center;
    }
    .rating-buy {
        background: linear-gradient(135deg, #059669, #10B981);
        color: white;
    }
    .rating-hold {
        background: linear-gradient(135deg, #D97706, #F59E0B);
        color: white;
    }
    .rating-sell {
        background: linear-gradient(135deg, #DC2626, #EF4444);
        color: white;
    }

    /* Metric Cards */
    .metric-card {
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.06);
        background: rgba(255,255,255,0.02);
        text-align: center;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #3B82F6;
    }
    .metric-label {
        font-size: 0.8rem;
        opacity: 0.6;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }

    /* Section Headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(59, 130, 246, 0.3);
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        opacity: 0.4;
        font-size: 0.85rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Streamlit tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# Session State
# ============================================
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "agent_statuses" not in st.session_state:
    st.session_state.agent_statuses = {}
if "is_running" not in st.session_state:
    st.session_state.is_running = False

# ============================================
# Sidebar
# ============================================
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    # Check for API keys
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    newsapi_key = os.getenv("NEWSAPI_KEY", "")

    if gemini_key:
        st.success("✅ Gemini API Key loaded")
    else:
        st.warning("⚠️ No Gemini API Key found")
        gemini_key = st.text_input("Enter Gemini API key:", type="password", key="gemini_input")
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
            st.rerun()

    if newsapi_key:
        st.success("✅ NewsAPI Key loaded")
    else:
        st.info("ℹ️ No NewsAPI Key (will use RSS fallback)")

    st.markdown("---")
    st.markdown("### 📋 About")
    st.markdown("""
    **TradeMind** uses 5 AI agents:
    1. 🗞️ **News Agent** — Sentiment analysis
    2. 📊 **Quant Agent** — Technical indicators
    3. 📑 **Fundamental Agent** — SEC filing RAG
    4. ⚠️ **Risk Agent** — Risk synthesis
    5. 📝 **Report Agent** — Report compilation

    Powered by **Gemini Flash** + **FAISS** + **sentence-transformers**
    """)

    st.markdown("---")
    st.markdown("### 🔗 Links")
    st.markdown("[📄 GitHub](https://github.com) · [📊 yfinance](https://pypi.org/project/yfinance/)")

# ============================================
# Main Content
# ============================================

# Hero
st.markdown("""
<div class="hero-container">
    <div class="hero-title">📊 TradeMind</div>
    <div class="hero-subtitle">AI-Powered Multi-Agent Equity Research Platform</div>
</div>
""", unsafe_allow_html=True)

# Ticker Input
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ticker_input = st.text_input(
        "Enter Stock Ticker",
        placeholder="e.g., AAPL, MSFT, TSLA, GOOGL",
        key="ticker_input",
        help="Enter a valid stock ticker symbol",
    )

    run_col1, run_col2 = st.columns(2)
    with run_col1:
        run_button = st.button(
            "🚀 Run Analysis",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.is_running,
        )
    with run_col2:
        clear_button = st.button("🗑️ Clear Results", use_container_width=True)

if clear_button:
    st.session_state.analysis_result = None
    st.session_state.agent_statuses = {}
    st.rerun()

# ============================================
# Run Analysis
# ============================================
if run_button and ticker_input:
    ticker = ticker_input.upper().strip()

    # Validate ticker format
    if not ticker.isalpha() or len(ticker) > 10:
        st.error("❌ Invalid ticker format. Use letters only (e.g., AAPL)")
    else:
        st.session_state.is_running = True
        st.session_state.agent_statuses = {}
        st.session_state.analysis_result = None

        # Progress display
        st.markdown(f"### 🔄 Analyzing **{ticker}**...")

        progress_bar = st.progress(0)
        status_container = st.container()

        agent_steps = [
            ("Fetching Company Info", "🏢"),
            ("News Agent: Analyzing Sentiment", "🗞️"),
            ("Quant Agent: Technical Analysis", "📊"),
            ("Fundamental Agent: SEC Filing RAG", "📑"),
            ("Risk Agent: Risk Assessment", "⚠️"),
            ("Report Agent: Compiling Report", "📝"),
        ]

        # Create status placeholders
        step_placeholders = {}
        with status_container:
            for step_name, emoji in agent_steps:
                step_placeholders[step_name] = st.empty()
                step_placeholders[step_name].markdown(
                    f'<div class="agent-card">⏳ {emoji} {step_name}</div>',
                    unsafe_allow_html=True,
                )

        def update_progress(description, step_index, total_steps, status):
            """Callback to update progress UI."""
            pct = (step_index + (1 if status == "done" else 0.5)) / total_steps
            progress_bar.progress(min(pct, 1.0))

            if description in step_placeholders:
                if status == "running":
                    emoji = dict(agent_steps).get(description, "⏳")
                    step_placeholders[description].markdown(
                        f'<div class="agent-card running">🔄 {emoji} {description} — Running...</div>',
                        unsafe_allow_html=True,
                    )
                elif status == "done":
                    emoji = dict(agent_steps).get(description, "✅")
                    step_placeholders[description].markdown(
                        f'<div class="agent-card done">✅ {emoji} {description} — Complete</div>',
                        unsafe_allow_html=True,
                    )
                elif status == "error":
                    emoji = dict(agent_steps).get(description, "❌")
                    step_placeholders[description].markdown(
                        f'<div class="agent-card error">❌ {emoji} {description} — Failed</div>',
                        unsafe_allow_html=True,
                    )

        # Run the pipeline
        try:
            result = run_analysis(ticker, progress_callback=update_progress)
            st.session_state.analysis_result = result
            progress_bar.progress(1.0)
            st.success(f"✅ Analysis complete for **{ticker}** in **{result['total_time']:.1f}s**!")
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            logger.error(f"Pipeline error: {e}", exc_info=True)
        finally:
            st.session_state.is_running = False

# ============================================
# Display Results
# ============================================
if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    context = result["context"]
    ticker = result["ticker"]

    report = context.get("report", {})
    company = context.get("company_info", {})
    news = context.get("news_analysis", {})
    quant = context.get("quant_analysis", {})
    fundamental = context.get("fundamental_analysis", {})
    risk_data = context.get("risk_analysis", {})

    st.markdown("---")

    # ---- Rating Header ----
    rating = report.get("investment_rating", "N/A")
    rating_class = {"BUY": "rating-buy", "HOLD": "rating-hold", "SELL": "rating-sell"}.get(rating, "")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; margin: 1rem 0;">
            <h2>{company.get('name', ticker)} ({ticker})</h2>
            <div class="rating-badge {rating_class}">{rating}</div>
            <p style="margin-top: 0.5rem; opacity: 0.7;">
                Confidence: {report.get('confidence_level', 'N/A')}/100 |
                Price Target: ${report.get('price_target', 'N/A')}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ---- Key Metrics Row ----
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("💰 Price", f"${company.get('current_price', 'N/A')}")
    with m2:
        st.metric("📈 Sentiment", f"{news.get('sentiment_score', 'N/A')}/100")
    with m3:
        signal = quant.get("trend_signal", quant.get("raw_indicators", {}).get("overall_signal", "N/A"))
        st.metric("📊 Technical", signal)
    with m4:
        st.metric("📑 Fundamental", f"{fundamental.get('fundamental_score', 'N/A')}/100")
    with m5:
        st.metric("⚠️ Risk", risk_data.get("overall_risk_score", "N/A"))

    st.markdown("---")

    # ---- Tabbed Report Viewer ----
    tab_report, tab_news, tab_tech, tab_fund, tab_risk, tab_raw = st.tabs([
        "📝 Full Report",
        "🗞️ News & Sentiment",
        "📊 Technicals",
        "📑 Fundamentals",
        "⚠️ Risk",
        "🔧 Raw Data",
    ])

    with tab_report:
        # Generate and display markdown report
        md_report = generate_markdown_report(ticker, context)
        st.markdown(md_report)

        # PDF Download
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            try:
                pdf_bytes = export_pdf(ticker, context)
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"TradeMind_{ticker}_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

    with tab_news:
        st.markdown("### 🗞️ News & Sentiment Analysis")

        if news and news.get("status") != "error":
            col1, col2 = st.columns(2)
            with col1:
                sentiment = news.get("overall_sentiment", "Neutral")
                score = news.get("sentiment_score", 50)
                emoji = {"Bullish": "🟢", "Bearish": "🔴", "Neutral": "🟡"}.get(sentiment, "⚪")
                st.markdown(f"**Overall Sentiment:** {emoji} {sentiment} ({score}/100)")

            with col2:
                st.markdown(f"**Articles Analyzed:** {news.get('articles_analyzed', 0)}")

            st.markdown(f"**Summary:** {news.get('sentiment_summary', 'N/A')}")

            # Key themes
            themes = news.get("key_themes", [])
            if themes:
                st.markdown("**Key Themes:**")
                for theme in themes:
                    st.markdown(f"- {theme}")

            # Risk flags
            flags = news.get("risk_flags", [])
            if flags:
                st.markdown("**⚠️ Risk Flags:**")
                for flag in flags:
                    st.markdown(f"- 🚩 {flag}")

            # Headlines
            headlines = news.get("headline_analysis", [])
            if headlines:
                st.markdown("**Headline Analysis:**")
                for h in headlines:
                    sent_emoji = {"Positive": "🟢", "Negative": "🔴", "Neutral": "🟡"}.get(h.get("sentiment", ""), "⚪")
                    st.markdown(f"- {sent_emoji} [{h.get('impact', '')}] {h.get('headline', '')}")
        else:
            st.info("No news data available for this ticker.")

    with tab_tech:
        st.markdown("### 📊 Technical Analysis")

        if quant and quant.get("status") != "error":
            st.markdown(f"**Trend Signal:** {quant.get('trend_signal', 'N/A')}")
            st.markdown(f"**Confidence:** {quant.get('confidence', 'N/A')}/100")
            st.markdown(f"**Summary:** {quant.get('technical_summary', 'N/A')}")

            raw = quant.get("raw_indicators", {})
            if raw:
                st.markdown("#### Indicator Details")

                # Display indicator table — all values as strings to avoid pyarrow type errors
                import pandas as pd
                indicator_data = {
                    "Indicator": ["RSI (14)", "MACD Line", "MACD Signal", "MACD Histogram",
                                  "Bollinger Upper", "Bollinger Lower", "50 SMA", "200 SMA",
                                  "Volatility (Ann.)"],
                    "Value": [
                        str(raw.get("rsi", {}).get("value", "N/A")),
                        str(raw.get("macd", {}).get("macd_line", "N/A")),
                        str(raw.get("macd", {}).get("signal_line", "N/A")),
                        str(raw.get("macd", {}).get("histogram", "N/A")),
                        f"${raw.get('bollinger', {}).get('upper', 'N/A')}",
                        f"${raw.get('bollinger', {}).get('lower', 'N/A')}",
                        f"${raw.get('sma', {}).get('sma_50', 'N/A')}",
                        f"${raw.get('sma', {}).get('sma_200', 'N/A')}",
                        f"{raw.get('volatility', {}).get('annualized_30d', 'N/A')}%",
                    ],
                    "Signal": [
                        str(raw.get("rsi", {}).get("signal", "N/A")),
                        str(raw.get("macd", {}).get("signal", "N/A")),
                        "—", "—",
                        str(raw.get("bollinger", {}).get("signal", "N/A")),
                        "—",
                        "—", str(raw.get("sma", {}).get("golden_cross", "N/A")),
                        str(raw.get("volatility", {}).get("signal", "N/A")),
                    ],
                }
                st.table(pd.DataFrame(indicator_data))

            # Indicator interpretations from LLM
            interp = quant.get("indicator_interpretation", {})
            if interp:
                st.markdown("#### LLM Interpretations")
                for key, val in interp.items():
                    st.markdown(f"**{key.replace('_', ' ').title()}:** {val}")
        else:
            st.info("No technical data available for this ticker.")

    with tab_fund:
        st.markdown("### 📑 Fundamental Analysis")

        if fundamental and fundamental.get("status") != "error":
            st.markdown(f"**Fundamental Score:** {fundamental.get('fundamental_score', 'N/A')}/100")
            st.markdown(f"**Summary:** {fundamental.get('fundamental_summary', 'N/A')}")
            st.markdown(f"**Data Sources:** {', '.join(fundamental.get('data_sources', []))}")

            for section_key, section_title in [
                ("revenue_growth", "📈 Revenue Growth"),
                ("margins", "💹 Margins"),
                ("debt_and_cash", "💰 Debt & Cash Position"),
                ("management_guidance", "🎯 Management Guidance"),
            ]:
                section = fundamental.get(section_key, {})
                if section:
                    st.markdown(f"#### {section_title}")
                    details = section.get("details", section.get("trend", "N/A"))
                    st.markdown(details)

            risks = fundamental.get("key_risks", [])
            if risks:
                st.markdown("#### ⚠️ Key Risks from Filings")
                for r in risks:
                    st.markdown(f"- {r}")
        else:
            st.info("No fundamental data available for this ticker.")

    with tab_risk:
        st.markdown("### ⚠️ Risk Assessment")

        if risk_data and risk_data.get("status") != "error":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Risk Level", risk_data.get("overall_risk_score", "N/A"))
            with col2:
                st.metric("30D Downside", f"{risk_data.get('downside_risk_30d_pct', 'N/A')}%")
            with col3:
                st.metric("30D Upside", f"{risk_data.get('upside_potential_30d_pct', 'N/A')}%")

            st.markdown(f"**Summary:** {risk_data.get('risk_summary', 'N/A')}")

            # Contradictions
            contradictions = risk_data.get("signal_contradictions", [])
            if contradictions:
                st.markdown("#### 🔀 Signal Contradictions")
                for c in contradictions:
                    st.warning(f"**{' vs '.join(c.get('signals', []))}:** {c.get('explanation', '')}")

            # Catalysts
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 🐻 Bear Catalysts")
                for c in risk_data.get("bear_catalysts", []):
                    st.markdown(f"- **{c.get('catalyst', '')}** (Prob: {c.get('probability', '')}, Impact: {c.get('impact', '')})")
            with col2:
                st.markdown("#### 🐂 Bull Catalysts")
                for c in risk_data.get("bull_catalysts", []):
                    st.markdown(f"- **{c.get('catalyst', '')}** (Prob: {c.get('probability', '')}, Impact: {c.get('impact', '')})")

            # Data completeness
            completeness = risk_data.get("data_completeness", {})
            if completeness:
                st.markdown("#### 📊 Data Completeness")
                for source, status in completeness.items():
                    emoji = {"Complete": "✅", "Missing": "❌", "Error": "⚠️", "No Data": "ℹ️"}.get(status, "❓")
                    st.markdown(f"- {emoji} {source}: {status}")
        else:
            st.info("No risk data available for this ticker.")

    with tab_raw:
        st.markdown("### 🔧 Raw Agent Outputs")
        st.markdown("Debug view of all agent outputs.")

        st.markdown(f"**Pipeline Time:** {result.get('total_time', 'N/A')}s")
        st.json(result.get("timings", {}))

        with st.expander("Company Info"):
            st.json(company)
        with st.expander("News Analysis"):
            st.json(news)
        with st.expander("Quant Analysis"):
            # Filter out large arrays for display
            quant_display = {k: v for k, v in quant.items() if k != "raw_indicators"} if quant else {}
            st.json(quant_display)
        with st.expander("Fundamental Analysis"):
            st.json(fundamental)
        with st.expander("Risk Analysis"):
            st.json(risk_data)
        with st.expander("Report"):
            st.json(report)

# ============================================
# Footer
# ============================================
st.markdown("""
<div class="footer">
    TradeMind © 2025 — AI-Powered Equity Research<br/>
    Built with Streamlit · Gemini Flash · FAISS · sentence-transformers
</div>
""", unsafe_allow_html=True)
