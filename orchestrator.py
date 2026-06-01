"""
TradeMind — Orchestrator
Runs the 5-agent pipeline sequentially, passing context between agents.
"""

import logging
import time
from typing import Callable, Optional

from tools.yfinance_tool import get_company_info
from agents.news_agent import NewsAgent
from agents.quant_agent import QuantAgent
from agents.fundamental_agent import FundamentalAgent
from agents.risk_agent import RiskAgent
from agents.report_agent import ReportAgent

logger = logging.getLogger("trademind.orchestrator")


# Pipeline steps
STEPS = [
    ("company_info", "Fetching Company Info", None),
    ("news_analysis", "News Agent: Analyzing Sentiment", NewsAgent),
    ("quant_analysis", "Quant Agent: Technical Analysis", QuantAgent),
    ("fundamental_analysis", "Fundamental Agent: SEC Filing RAG", FundamentalAgent),
    ("risk_analysis", "Risk Agent: Risk Assessment", RiskAgent),
    ("report", "Report Agent: Compiling Report", ReportAgent),
]


def run_analysis(
    ticker: str,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """
    Run the full TradeMind analysis pipeline.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        progress_callback: Optional callback(step_name, step_index, total_steps, status)

    Returns:
        Dict with all agent outputs and final report
    """
    ticker = ticker.upper().strip()
    total_steps = len(STEPS)
    context = {}
    timings = {}

    logger.info(f"{'='*60}")
    logger.info(f"🚀 Starting TradeMind analysis for {ticker}")
    logger.info(f"{'='*60}")

    pipeline_start = time.time()

    for i, (key, description, agent_class) in enumerate(STEPS):
        step_start = time.time()

        # Report progress
        if progress_callback:
            progress_callback(description, i, total_steps, "running")

        logger.info(f"\n--- Step {i+1}/{total_steps}: {description} ---")

        try:
            if key == "company_info":
                # Special case: fetch company info directly
                result = get_company_info(ticker)
            else:
                # Run agent
                agent = agent_class()
                result = agent.run(ticker, context)

            context[key] = result
            elapsed = time.time() - step_start
            timings[key] = round(elapsed, 2)

            logger.info(f"✅ {description} completed in {elapsed:.1f}s")

            if progress_callback:
                progress_callback(description, i, total_steps, "done")

        except Exception as e:
            elapsed = time.time() - step_start
            timings[key] = round(elapsed, 2)
            logger.error(f"❌ {description} failed after {elapsed:.1f}s: {e}")

            context[key] = {"status": "error", "error": str(e)}

            if progress_callback:
                progress_callback(description, i, total_steps, "error")

            # Continue pipeline even if an agent fails (graceful degradation)
            if key == "report":
                # Report agent failure is critical — can't continue
                raise

    total_time = time.time() - pipeline_start

    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 TradeMind analysis for {ticker} completed in {total_time:.1f}s")
    logger.info(f"Timings: {timings}")
    logger.info(f"{'='*60}")

    return {
        "ticker": ticker,
        "context": context,
        "timings": timings,
        "total_time": round(total_time, 2),
    }
