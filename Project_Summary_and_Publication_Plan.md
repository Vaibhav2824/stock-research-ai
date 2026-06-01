# TradeMind: Multi-Agent AI Equity Research Platform

## 1. What Have We Made?
We have developed **TradeMind**, an end-to-end, multi-agent AI equity research platform that autonomously synthesizes institutional-grade financial reports. The system mitigates the "hallucination problem" of standard LLMs by strictly orchestrating domain-specific agents bounded by real-world financial endpoints. 

The architecture consists of:
*   **Fundamental Agent (RAG-based):** Ingests, chunks, and embeds massive SEC EDGAR filings (10-K/10-Q) using Google Gemini Embeddings and FAISS local vector databases to accurately retrieve financial metrics and management guidance.
*   **Quant Agent (Deterministic + LLM Interpretation):** Fetches real-time market data via `yfinance`, calculates deterministic technical indicators locally (RSI, MACD, Bollinger Bands, SMAs), and feeds the matrix to an LLM to interpret structural trends.
*   **News Agent (Sentiment Analysis):** Aggregates real-time news headlines to perform granular sentiment NLP classification and extract catalyst themes.
*   **Risk Agent:** Synthesizes the outputs of the previous agents to locate contradictions (e.g., strong technicals but weakening fundamentals) and assigns a probabilistic risk score.
*   **Report Agent & Orchestrator:** Manages the entire pipeline via a master timeline, handles dynamic LLM fallback/load-balancing (between Google GenAI, Groq, and OpenRouter), and compiles a professional Markdown/PDF export via ReportLab within a fully responsive Streamlit dashboard.

---

## 2. What Is The Novelty?
The novelty of this project lies in its **Hybrid Agentic Workflow with Deterministic Grounding**:
1.  **Separation of Concerns:** Instead of asking a single monolithic LLM to "analyze a stock," TradeMind forces specialized agents to look *only* at specific data vectors (Technicals, News, SEC Filings), reducing hallucinations and forced-correlations.
2.  **Deterministic + Heuristic Blending:** LLMs are notoriously bad at math. The Quant Agent calculates complex mathematical indicators locally in native Python (`ta` library) and *only* relies on the LLM to interpret the final numerical payload.
3.  **Cross-Agent Contradiction Checking:** The Risk Agent specifically compares the outputs of sibling agents to find divergences—mimicking how human institutional analysts operate (e.g., identifying when retail sentiment blindly ignores SEC 10-K risk warnings).
4.  **Resilient Cost-Optimized Routing:** The LLM factory layer implements a dynamic cascading rate-limit strategy, bouncing between free-tier APIs (Gemini 2.0 Flash → Groq Llama-3 → OpenRouter Nemotron) adjusting token contexts automatically to guarantee zero-cost production scaling.

---

## 3. How Can We Publish a Paper Based on This Project?
To publish this as a research paper, we need to frame it academically as a contribution to **"LLM Applications in Quantitative Trading & Fundamental Finance."**

*   **Target Venues:** IEEE Conferences (e.g., IEEE CIFEr), ACM International Conference on AI in Finance (ICAIF), or specialized NeurIPS/AAAI workshops relating to LLMs in Finance.
*   **Core Research Question:** *Does multi-agent orchestration paired with quantitative deterministic grounding outperform single-prompt monolithic LLM financial forecasting?*
*   **Methodology to add before publishing:**
    1.  **Backtesting:** Run the pipeline retroactively on 50 stocks from exactly 1 year ago. Compare TradeMind's generated "Price Targets" and "Bull/Bear metrics" with the actual performance of the stock over the last 12 months.
    2.  **Ablation Study:** Prove that the RAG component is necessary. Run the report generation *without* the Fundamental SEC Agent and measure the drop in factual accuracy.
    3.  **Metrics:** Track execution time, token optimization success rates, and RAG retrieval latency. 

* **Proposed Paper Title:** *TradeMind: A Multi-Agentic Architecture for Deterministically Grounded Financial Research and SEC Retrieval-Augmented Generation.*

---

## 4. Division of Work (For 3 People)
To accurately tell your professor who did what without overlapping heavily, you should divide the narrative of the completed application into three distinct pillars: Backend RAG, Algorithmic/Data Processing, and Orchestration/UI.

**Student 1: RAG Architect & Fundamental Operations**
*   **Responsibilities:** SEC EDGAR integration pipeline and Retrieval-Augmented Generation (RAG).
*   **Code Ownership:** `edgar_tool.py`, `rag/embedder.py`, `rag/indexer.py`, `rag/retriever.py`, and `fundamental_agent.py`.
*   **Contribution:** Handled the ingestion of massive 10-K SEC text blobs, implemented the FAISS vector database chunking mechanisms, and fine-tuned the Gemini embedding configurations to ensure the LLM could accurately read management guidance without exceeding token limitations.

**Student 2: Quantitative Data & NLP Sentiment Analyst**
*   **Responsibilities:** Real-time data fetching, mathematical indicator computation, and news sentiment classification.
*   **Code Ownership:** `yfinance_tool.py`, `news_tool.py`, `quant_agent.py`, and `news_agent.py`.
*   **Contribution:** Built the deterministic financial math engines ensuring the LLM didn't "hallucinate" math. Calculated RSI, MACD, and SMA crossovers locally. Built the heuristic logic to parse real-time financial news, format the context windows, and grade sentiment probability.

**Student 3: Lead Systems Orchestrator & UI Interface Designer**
*   **Responsibilities:** Multi-agent asynchronous pipeline, LLM network engineering, and frontend application.
*   **Code Ownership:** `orchestrator.py`, `config.py`, `base_agent.py`, `report_agent.py`, `app.py`, and `report/pdf_export.py`.
*   **Contribution:** Designed the overarching State Machine that lets agents talk to one another. Engineered the resilient `config.py` LLM-factory API routers (handling Rate Limits and Gemini/Groq API fallbacks) allowing the app to run freely. Built the entire interactive Streamlit UI and the dynamic PDF generation algorithms.

---

## 5. Complete Execution Workflow
Understanding how data flows through the application is critical for demonstrating the robustness of your multi-agent architecture. Here is the step-by-step pipeline execution when a user submits a ticker (e.g., `AAPL`):

1.  **Frontend Initialization (`app.py`):** The user enters the ticker. Streamlit triggers the main analysis execution sequence.
2.  **API Data Pre-fetch:** Raw endpoints fetch the baseline numbers: Yahoo Finance downloads 1-3 years of quantitative price tables. NewsAPI/Feedparser grabs the last 50-100 news articles. SEC EDGAR downloads the raw XBRL/HTML 10-K document.
3.  **RAG Embedding Phase (`rag/*`):** The SEC document is too large for an LLM. The `indexer.py` slices the document into 1,000-character chunks. The `embedder.py` passes these chunks to Gemini to create floating-point vector coordinates. The chunks and vectors are stored in a FAISS index.
4.  **Parallel Agent Execution (`orchestrator.py` & `agents/*`):**
    *   **Quant Agent:** Computes indicators (RSI, SMAs). Sends the numeric trend matrix to the LLM. LLM replies with a technical interpretation.
    *   **News Agent:** Groups the articles, sends them to the LLM. LLM assigns a 1-100 sentiment score based on the textual reality of the headlines.
    *   **Fundamental Agent:** Queries the RAG FAISS index for "Revenue Strategy" and "Risks". Returns the 5 most relevant chunks. The LLM reads only those chunks to write the Fundamental Analysis.
5.  **Risk Synthesis Pipeline (`risk_agent.py`):** The Risk Agent is deliberately injected here. It receives all previous agent outputs and looks for anomalies (e.g., Sentiment says BUY, but the Fundamental Agent flagged a massive SEC debt risk).
6.  **Report Generation (`report_agent.py`):** The Report Agent receives all finalized context windows. Guided by a strict JSON-enforced schema, it writes the final institutional summary and prices a target.
7.  **Dashboard Rendering (`app.py` & `report/generator.py`):** Streamlit parses the JSON into readable UI metrics. `pdf_export.py` converts the text into a downloadable ReportLab PDF.

---

## 6. Comprehensive File Directory Guide
When explaining the architecture, you can reference this file breakdown:

### Core Framework (Root)
| File | Role |
| :--- | :--- |
| `app.py` | The main graphical user interface built on Streamlit. Displays sliders, text fields, tabs, and rendered markdown elements. |
| `orchestrator.py` | The central command hub. It runs the main `run_analysis` loop, enforcing the order in which agents execute and passing their output payloads securely. |
| `config.py` | The custom "LLM Factory". Handles loading API keys (`.env`) and implements failover logic with exponential rate-limit backoffs (Gemini \u2192 Groq \u2192 OpenRouter). |

### Autonomous Agents (`/agents`)
| File | Role |
| :--- | :--- |
| `base_agent.py` | The parent blueprint enforcing how agents communicate with LLMs and robustly extracting / cleaning JSON responses. |
| `quant_agent.py` | Uses mathematical modeling to gauge statistical market trends (Momentum, Volatility). |
| `news_agent.py` | Uses structural NLP extraction to judge retail and institutional sentiment toward the asset. |
| `fundamental_agent.py` | Interfaces uniquely with the FAISS local database to interpret raw inner-corporate SEC filings without hallucinating. |
| `risk_agent.py` | Acts as the system auditor. Synthesizes anomalies and contradictions between structural agents. |
| `report_agent.py` | The overarching compiler that assembles the cohesive, multi-format financial report. |

### RAG System (`/rag`)
| File | Role |
| :--- | :--- |
| `embedder.py` | Converts plaintext 10-K sections into high-dimensional vectors via Google Gemini. |
| `indexer.py` | Stores vector embeddings using Facebook's underlying C++ similarity search library (`faiss-cpu`). |
| `retriever.py` | Pulls the top-K highest similarity chunks based on a specific prompt (like "What are the legal risks?"). |

### Utilities (`/tools` & `/report`)
| File | Role |
| :--- | :--- |
| `edgar_tool.py`, `news_tool.py`, `yfinance_tool.py` | Scraping tools bridging Python with the external live-world internet. |
| `generator.py`, `pdf_export.py` | Final assembly mechanisms generating markdown strings and PDF binary files using `reportlab`. |

---

## 7. Recommended Validation Stocks 
During a presentation or demonstration, your multi-agent system runs optimally on large-cap, highly liquid equities that have robust active news cycles, publicly updated SEC records, and smooth technical histories. 

**Here are 10 stocks where TradeMind performs perfectly:**
1.  **AAPL (Apple Inc.):** Classic mega-cap, massive historical data, incredibly stable technicals.
2.  **MSFT (Microsoft Corp.):** Massive structural fundamentals; usually produces extremely insightful Fundamental/SEC analysis.
3.  **NVDA (NVIDIA Corp.):** High volatility, extreme momentum. Great for demonstrating the Quant Agent's bullish trend-catching algorithms.
4.  **TSLA (Tesla Inc.):** A highly narrative-driven stock. Perfect for showcasing the News Agent extracting polarizing bull/bear sentiment.
5.  **AMZN (Amazon.com Inc.):** Vast operational revenue. Shows the RAG tool capturing massive supply-chain and cloud data context.
6.  **GOOGL (Alphabet Inc.):** Consistent regulatory news mixed with solid technicals; triggers phenomenal Risk Agent outputs.
7.  **META (Meta Platforms):** Demonstrates volatility recoveries and strong ad-revenue fundamental insights within the SEC filings.
8.  **JPM (JPMorgan Chase & Co):** Best test for standard institutional banking analysis—relies heavily on the RAG pulling exact interest rate parameters and debt risks.
9.  **JNJ (Johnson & Johnson):** Very low-beta, defensive stock. Proves the Quant platform recognizes stability and low downside risks.
10. **DIS (Walt Disney Co):** High retail sentiment clashes with complex fundamental restructuring; tests the Risk Agent's contradiction engines perfectly.
