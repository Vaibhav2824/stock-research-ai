# 📊 TradeMind
### *Because your portfolio deserves more than a gut feeling.*

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_Flash-2.0-4285F4?style=for-the-badge&logo=google&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-RAG_Enabled-00B4D8?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)

**5 AI agents. 1 ticker. A full equity research report in under 90 seconds.**

[🚀 Quickstart](#-quickstart) · [🏗️ Architecture](#️-architecture) · [🤖 Agents](#-the-5-agent-pipeline) · [📡 RAG Pipeline](#-rag-pipeline) · [⚙️ Configuration](#️-configuration)

</div>

---

## What is TradeMind?

TradeMind is a multi-agent AI system that does in 90 seconds what a junior equity analyst does in 3 days.

You type a ticker. Five specialized AI agents fan out in parallel — scraping news, computing technical indicators, reading SEC filings, synthesizing risk, and writing a full report. The result: a **professional-grade equity research report** with an investment rating, price target, and narrative analysis — downloadable as a PDF.

No Bloomberg terminal. No Wall Street access. Just a free Gemini API key.

```
Input:  AAPL
Output: 8-page equity research report with BUY/HOLD/SELL rating,
        price target, technicals, fundamentals, risk assessment,
        and investment thesis. PDF included.
Time:   ~60–90 seconds
Cost:   $0 (free tier APIs)
```

---

## ✨ Features

| | Feature | Details |
|-|---------|---------|
| 🤖 | **5-Agent Pipeline** | News → Quant → Fundamental → Risk → Report, with full context sharing |
| 📑 | **SEC EDGAR RAG** | Downloads 10-K/10-Q filings, chunks + embeds with FAISS, retrieves via semantic search |
| 📊 | **Technical Analysis** | RSI, MACD, Bollinger Bands, SMA 50/200, annualized volatility — all computed locally |
| 🗞️ | **News Sentiment** | NewsAPI primary → Yahoo Finance RSS → Google News RSS fallback chain |
| 📄 | **PDF Export** | ReportLab-generated institutional-style report with tables, rating badges, and full sections |
| 🛡️ | **Graceful Degradation** | Every agent has error handling + mock fallbacks — the demo never crashes |
| 🌑 | **Dark UI** | Premium Streamlit interface with live agent progress, tabbed viewer, one-click PDF download |
| ⚡ | **FAISS Caching** | Ticker indexes cached to disk — re-runs are instant, no re-embedding |
| 🔁 | **LLM Fallback Chain** | Gemini → Groq → OpenRouter → hardcoded mock. Something always works. |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        app.py                               │
│                    Streamlit UI                             │
│         (Dark theme · Live progress · PDF download)         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   orchestrator.py                           │
│              Sequential Pipeline Runner                     │
│         (Context dict passed between all agents)            │
└──┬──────────┬──────────┬──────────┬──────────┬─────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌───────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Co.  │ │ News  │ │ Quant  │ │ Fund.  │ │ Risk   │
│ Info │ │ Agent │ │ Agent  │ │ Agent  │ │ Agent  │
│      │ │       │ │        │ │        │ │        │
│yfin  │ │NewsAPI│ │yfinance│ │EDGAR   │ │All     │
│      │ │Yahoo  │ │ta lib  │ │FAISS   │ │prior   │
│      │ │Google │ │LLM     │ │RAG+LLM │ │outputs │
└──────┘ └───────┘ └────────┘ └────────┘ └────────┘
                                                   │
                                                   ▼
                                          ┌────────────────┐
                                          │  Report Agent  │
                                          │                │
                                          │ Markdown + PDF │
                                          │ BUY/HOLD/SELL  │
                                          │ Price Target   │
                                          └────────────────┘
```

All agents extend `BaseAgent` — a shared abstract class with unified LLM calls, JSON extraction with fallbacks, retry logic with exponential backoff, and structured logging.

---

## 🤖 The 5-Agent Pipeline

### Agent 1 — 🏢 Company Info
*Not an LLM agent. Pure data fetch.*
- Pulls live metadata from yfinance: name, sector, industry, market cap, current price, P/E, 52-week high/low
- Seeds the context dict that every downstream agent reads

### Agent 2 — 🗞️ News Agent
*"What is the world saying about this stock right now?"*
- Fetches up to 20 recent articles via **NewsAPI → Yahoo Finance RSS → Google News RSS** (tried in order)
- Sends article titles + summaries to Gemini with a structured system prompt
- Returns: `overall_sentiment`, `sentiment_score` (0–100), `key_themes`, `risk_flags`, `headline_analysis`

### Agent 3 — 📊 Quant Agent
*"What are the charts saying?"*
- Downloads 1 year of OHLCV data via yfinance
- Computes all indicators locally using the `ta` library: RSI(14), MACD(12,26,9), Bollinger Bands(20,2), SMA(50), SMA(200), 30-day annualized volatility
- Sends raw indicator values to Gemini for interpretation
- Returns: `trend_signal` (Strong Buy → Strong Sell), `confidence`, `support_level`, `resistance_level`, full interpretations

### Agent 4 — 📑 Fundamental Agent
*"What do the actual filings say?"*
- Downloads the latest 10-K (falls back to 10-Q) from **SEC EDGAR**
- Runs the full **RAG pipeline** (see below) to extract relevant excerpts
- Supplements with yfinance financial statements (revenue, net income, debt, cash)
- Returns: `fundamental_score` (0–100), revenue/margin/debt/guidance analysis, `key_risks`

### Agent 5 — ⚠️ Risk Agent
*"Where can this go wrong — and how wrong?"*
- Receives the full outputs of all three prior agents as context
- Cross-references signals for contradictions (e.g. bullish technicals + negative news)
- Returns: `overall_risk_score`, `signal_contradictions`, `bear_catalysts`, `bull_catalysts`, `downside_risk_30d_pct`, `upside_potential_30d_pct`

### Agent 6 — 📝 Report Agent
*"Write the Goldman Sachs memo."*
- Compiles the entire context into a structured prompt
- System prompt instructs it to write as a senior Goldman Sachs equity analyst
- Returns: `investment_rating` (BUY/HOLD/SELL), `confidence_level`, `price_target`, full narrative sections, bull/bear cases
- Feeds `report/generator.py` (Markdown) and `report/pdf_export.py` (ReportLab PDF)

---

## 📡 RAG Pipeline

The Fundamental Agent runs a complete vector-search RAG system over SEC filings — entirely free.

```
SEC EDGAR 10-K/10-Q
        │
        ▼
  ┌─────────────┐
  │   Chunker   │  512-word chunks, 50-word overlap
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Embedder   │  gemini-embedding-001 (3072-dim)
  │             │  → TF-IDF hash fallback if quota hit
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │    FAISS    │  IndexFlatIP (cosine similarity
  │   Indexer   │  via dot product on L2-normalized vecs)
  └──────┬──────┘
         │   Persisted to cache/{TICKER}_index.faiss
         ▼        +  cache/{TICKER}_chunks.pkl
  ┌─────────────┐
  │  Retriever  │  5 targeted queries:
  │             │  · "revenue growth trend"
  │             │  · "gross margin and operating margin"
  │             │  · "total debt and cash position"
  │             │  · "management forward guidance"
  │             │  · "key risk factors"
  └──────┬──────┘
         │  Top 3 chunks per query → deduplicated → max 15 chunks
         ▼
  ┌─────────────┐
  │   Context   │  Injected into Fundamental Agent prompt
  │   Builder   │  alongside yfinance financial statements
  └─────────────┘
```

**Why FAISS instead of a vector DB?**
Zero infrastructure. No Pinecone account, no Docker, no API key. The index lives on disk and loads in milliseconds. For a single-ticker research pipeline, it's the right tool.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- A free [Google AI Studio](https://aistudio.google.com) account for `GEMINI_API_KEY`

### 1. Clone

```bash
git clone https://github.com/your-username/trademind.git
cd trademind
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
# REQUIRED
GEMINI_API_KEY=your_gemini_api_key_here
EDGAR_USER_AGENT=Your Name your@email.com

# OPTIONAL (RSS fallbacks work without these)
NEWSAPI_KEY=your_newsapi_key_here
GROQ_API_KEY=your_groq_key_here
```

### 4. Run

```bash
streamlit run app.py
```

Go to **http://localhost:8501**, type any ticker (`AAPL`, `NVDA`, `RELIANCE.NS`), hit **Run Analysis**. Done.

---

## ⚙️ Configuration

### API Keys

| Variable | Required | Purpose | Free Tier | Get it |
|----------|----------|---------|-----------|--------|
| `GEMINI_API_KEY` | ✅ | LLM + Embeddings | 15 RPM · 1M TPD | [aistudio.google.com](https://aistudio.google.com) |
| `EDGAR_USER_AGENT` | ✅ | SEC EDGAR access | Free (name + email) | Just set `"Name email"` |
| `NEWSAPI_KEY` | ❌ | News articles | 100 req/day | [newsapi.org](https://newsapi.org) |
| `GROQ_API_KEY` | ❌ | LLM fallback | 30 RPM · 14.4K RPD | [console.groq.com](https://console.groq.com) |
| `OPENROUTER_API_KEY` | ❌ | LLM fallback #2 | Free models | [openrouter.ai](https://openrouter.ai) |

### LLM Fallback Chain

```
Primary:    Gemini Flash 2.0      (4.1s throttle → safe under 15 RPM)
Fallback 1: Groq Llama 3.3 70B   (fast + free)
Fallback 2: OpenRouter            (gemma-2-9b → llama-3.1-8b → zephyr-7b → mistral-nemo)
Last resort: Hardcoded mock data  (demo never crashes)
```

### Environment Variables

```env
LLM_PROVIDER=gemini          # gemini | groq | openrouter
LLM_MODEL=gemini-2.0-flash
MAX_TOKENS=4096
LOG_LEVEL=INFO               # DEBUG | INFO | WARNING | ERROR
```

---

## 📁 Project Structure

```
trademind/
│
├── 📄 app.py                    # Streamlit UI — dark theme, tabbed viewer, PDF download
├── 📄 orchestrator.py           # Pipeline runner — sequential execution, context passing
├── 📄 config.py                 # LLM factory — provider chain, API key loading, throttling
│
├── 🤖 agents/
│   ├── base_agent.py            # Abstract base — LLM calls, JSON parsing, retry logic
│   ├── news_agent.py            # Sentiment analysis from news articles
│   ├── quant_agent.py           # Technical indicators + LLM interpretation
│   ├── fundamental_agent.py     # SEC filing RAG + financial statement analysis
│   ├── risk_agent.py            # Cross-signal risk synthesis
│   └── report_agent.py          # Final report compilation
│
├── 🛠️ tools/
│   ├── yfinance_tool.py         # OHLCV data, company info, financial statements
│   ├── ta_tool.py               # RSI, MACD, Bollinger, SMA, volatility computation
│   ├── edgar_tool.py            # SEC EDGAR CIK lookup + filing download + HTML parsing
│   └── news_tool.py             # NewsAPI + Yahoo RSS + Google News RSS
│
├── 🔍 rag/
│   ├── embedder.py              # Gemini embedding-001 + TF-IDF hash fallback
│   ├── indexer.py               # FAISS IndexFlatIP builder + disk persistence
│   └── retriever.py             # Single-query + multi-query semantic retrieval
│
├── 📋 report/
│   ├── generator.py             # Markdown report builder with safe nested dict access
│   └── pdf_export.py            # ReportLab PDF — custom styles, tables, rating badges
│
├── 📦 cache/                    # Auto-created. Stores {TICKER}_index.faiss + _chunks.pkl
├── 📦 reports/                  # Auto-created. Stores generated PDFs
│
├── 📄 requirements.txt
├── 📄 .env.example
└── 📄 .gitignore
```

---

## 🖥️ UI Overview

The Streamlit app has six tabs per analysis:

| Tab | Content |
|-----|---------|
| 📝 **Full Report** | Complete markdown narrative + PDF download button |
| 🗞️ **News & Sentiment** | Score, themes, risk flags, headline-by-headline breakdown |
| 📊 **Technicals** | Signal, confidence, full indicator table, LLM interpretations |
| 📑 **Fundamentals** | Score, revenue/margin/debt/guidance sections, filing risks |
| ⚠️ **Risk** | Risk level, downside/upside %, contradictions, bull/bear catalysts |
| 🔧 **Raw Data** | Full JSON from every agent + pipeline timings (debug view) |

---

## ⏱️ Performance

| Step | Typical Time |
|------|-------------|
| Company info fetch | ~1s |
| News fetch + analysis | ~8–12s |
| Technical analysis | ~5–8s |
| SEC filing download | ~10–20s |
| FAISS index build (first run) | ~15–30s |
| FAISS index load (cached) | ~0.5s |
| Risk analysis | ~6–10s |
| Report generation | ~8–12s |
| **Total (cold)** | **~60–90s** |
| **Total (warm cache)** | **~40–55s** |

> Gemini's free tier throttle (4.1s/call) accounts for most of the wait time. With a paid key, total time drops to ~20–30s.

---

## 🌍 Ticker Support

| Market | Example | Notes |
|--------|---------|-------|
| US Stocks | `AAPL`, `NVDA`, `TSLA` | Full support including SEC filings |
| US ETFs | `SPY`, `QQQ`, `VTI` | No SEC filing; other agents work normally |
| Indian NSE | `RELIANCE.NS`, `TCS.NS` | No SEC filing; news + technicals work |
| London | `SHEL.L`, `HSBA.L` | No SEC filing; news + technicals work |
| Crypto | `BTC-USD` | Technical + news work; fundamentals limited |

SEC EDGAR integration only applies to US-listed companies. For all others, the Fundamental Agent gracefully skips the RAG step and relies on yfinance financial statements alone.

---

## 🔧 Development

### Running in debug mode

```bash
LOG_LEVEL=DEBUG streamlit run app.py
```

### Clearing the FAISS cache

```bash
rm cache/*.faiss cache/*.pkl
```

### Testing individual agents

```python
from agents.news_agent import NewsAgent

agent = NewsAgent()
result = agent.run("AAPL", context={"company_info": {"name": "Apple Inc."}})
print(result["overall_sentiment"], result["sentiment_score"])
```

### Adding a new agent

1. Create `agents/your_agent.py` extending `BaseAgent`
2. Implement `run(self, ticker, context) -> dict`
3. Add to `STEPS` list in `orchestrator.py`
4. Add output key to `report_agent.py`'s context builder

---

## 📦 Dependencies

```
streamlit>=1.38.0          # UI framework
google-generativeai>=0.8.0 # Gemini LLM + embeddings
groq>=0.11.0               # Groq LLM fallback
yfinance>=0.2.40           # Market data
ta>=0.11.0                 # Technical indicators
faiss-cpu>=1.8.0           # Vector similarity search
reportlab>=4.2.0           # PDF generation
feedparser>=6.0.11         # RSS feed parsing
beautifulsoup4>=4.12.0     # SEC filing HTML parsing
requests>=2.32.0           # HTTP client
python-dotenv>=1.0.1       # Environment variable loading
numpy>=1.26.0
pandas>=2.2.0
```

---

## ⚠️ Known Limitations

- **Rate limits**: Gemini free tier is 15 RPM. The 4.1s throttle keeps you safe, but running multiple tickers back-to-back quickly may still hit quota errors. Wait ~60s between runs if that happens.
- **SEC filings**: Some smaller companies or recent IPOs may not have filings indexed in EDGAR yet. The agent handles this gracefully.
- **News quality**: Without a `NEWSAPI_KEY`, RSS feeds may return older or less relevant articles. Results improve significantly with a paid key.
- **Price targets**: LLM-generated price targets are based on narrative analysis, not DCF models. Treat them as directional, not precise.
- **Python 3.14**: `sentence-transformers` crashes on Python 3.14. The `gemini-embedding-001` path avoids this entirely; TF-IDF hash fallback covers the rest.

---

## 📜 Disclaimer

TradeMind is an educational and research tool. **Nothing it produces constitutes financial or investment advice.** The AI-generated ratings, price targets, and analysis are for informational purposes only. Always consult a qualified financial advisor and do your own due diligence before making any investment decisions.

Past performance is not indicative of future results. The developers are not responsible for any financial losses incurred through use of this software.

---

## 📄 License

MIT License — free to use, modify, and distribute. See `LICENSE` for details.

---

<div align="center">

Built with 🤖 **Google Gemini** · 📊 **FAISS** · 📄 **ReportLab** · 📈 **yfinance** · 🎨 **Streamlit**

*If this saved you time, drop a ⭐ on GitHub.*

</div>
