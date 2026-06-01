# TradeMind — Project Progress Tracker

> Course: UE23AM343BA2 | Last Updated: 2026-04-11

## Project Overview

Multi-agent AI stock research platform. Users enter a ticker, get a
professional equity research report in < 60 seconds.

**Stack:** Streamlit · Python · Gemini Flash · FAISS · sentence-transformers · ReportLab

## MVP Scope

- ✅ Stock ticker input with validation
- ✅ News Agent: fetches + summarizes stock news sentiment
- ✅ Quant Agent: computes RSI / MACD / Bollinger + trend signal
- ✅ Fundamental Agent: retrieves SEC filings and does RAG summary
- ✅ Risk Agent: synthesizes red flags from all agent outputs
- ✅ Report Agent: generates professional markdown equity research report
- ✅ PDF download of final report
- ✅ Polished Streamlit UI with progress tracking

## Folder Structure

```
LLM-PROJECT/
├── app.py                  # Streamlit UI
├── config.py               # Settings + LLM factory
├── orchestrator.py         # Agent pipeline
├── agents/                 # 5 AI agents
├── tools/                  # Data fetching tools
├── rag/                    # FAISS RAG pipeline
├── report/                 # Report generation + PDF
├── cache/                  # Disk cache (gitignored)
└── tests/                  # Test suite
```

## Progress Checklist

### Phase 1: Foundation
- [ ] Environment setup (.env, requirements)
- [ ] Config module with LLM factory
- [ ] Install dependencies

### Phase 2: Tools
- [ ] yfinance tool (OHLCV + company info)
- [ ] Technical analysis tool (RSI, MACD, Bollinger)
- [ ] News tool (NewsAPI + RSS fallback)
- [ ] SEC EDGAR tool (filing download)

### Phase 3: RAG Pipeline
- [ ] sentence-transformers embedder
- [ ] FAISS indexer
- [ ] RAG retriever

### Phase 4: Agents
- [ ] Base agent class
- [ ] News Agent
- [ ] Quant Agent
- [ ] Fundamental Agent
- [ ] Risk Agent
- [ ] Report Agent

### Phase 5: Integration
- [ ] Orchestrator (sequential pipeline)
- [ ] Markdown report generator
- [ ] PDF exporter
- [ ] Streamlit UI

### Phase 6: Testing
- [ ] End-to-end test on AAPL
- [ ] PDF download works
- [ ] Error handling edge cases
- [ ] Test with 3+ tickers

## Blocker Log

| ID | Issue | Status | Resolution |
|----|-------|--------|------------|
| — | None yet | — | — |

## Testing Checklist

- [ ] Each tool returns valid data for AAPL
- [ ] RAG embeds + retrieves correctly
- [ ] Each agent returns valid JSON
- [ ] Full pipeline completes < 120s
- [ ] PDF generates and opens correctly
- [ ] UI renders all sections
- [ ] Handles invalid ticker gracefully
- [ ] Handles API failures gracefully

## Deployment Checklist

- [ ] requirements.txt up to date
- [ ] .env.example has all required vars
- [ ] App runs with `streamlit run app.py`
- [ ] Test on Streamlit Cloud
- [ ] README polished
