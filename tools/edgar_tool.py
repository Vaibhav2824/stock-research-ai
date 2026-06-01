"""
TradeMind — SEC EDGAR Tool
Downloads SEC filings (10-K, 10-Q) from the EDGAR full-text search API.
Free, no auth needed. Rate limited to 10 requests/sec.
"""

import logging
import os
import time
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("trademind.tools.edgar")

EDGAR_USER_AGENT = os.getenv("EDGAR_USER_AGENT", "TradeMind research@trademind.dev")

# SEC EDGAR EFTS (full-text search) API
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_FILING_URL = "https://www.sec.gov/Archives/edgar/data"

# Headers required by SEC
HEADERS = {
    "User-Agent": EDGAR_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
}


def download_filing(ticker: str, filing_type: str = "10-K", max_retries: int = 3) -> str:
    """
    Download the latest SEC filing text for a ticker.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        filing_type: "10-K" (annual) or "10-Q" (quarterly)
        max_retries: Number of retries on failure

    Returns:
        Plain text content of the filing (truncated to ~50K chars for RAG)
    """
    logger.info(f"Downloading {filing_type} for {ticker} from SEC EDGAR...")

    for attempt in range(max_retries):
        try:
            # Step 1: Get CIK number for ticker
            cik = _get_cik(ticker)
            if not cik:
                logger.warning(f"Could not find CIK for {ticker}")
                return ""

            # Step 2: Get latest filing URL
            filing_url = _get_latest_filing_url(cik, filing_type)
            if not filing_url:
                logger.warning(f"No {filing_type} filing found for {ticker}")
                return ""

            # Step 3: Download and parse filing
            text = _download_and_parse(filing_url)
            if text:
                # Truncate to ~50K chars for RAG (keeps things manageable)
                text = text[:50000]
                logger.info(f"Downloaded {filing_type} for {ticker}: {len(text)} chars")
                return text

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            time.sleep(1)  # Respect rate limits

    logger.error(f"Failed to download {filing_type} for {ticker} after {max_retries} attempts")
    return ""


def _get_cik(ticker: str) -> str:
    """Look up CIK number for a ticker symbol."""
    url = "https://www.sec.gov/cgi-bin/browse-edgar"
    params = {
        "company": "",
        "CIK": ticker,
        "type": "",
        "dateb": "",
        "owner": "include",
        "count": "1",
        "search_text": "",
        "action": "getcompany",
        "output": "atom",
    }

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()

        # Try the company tickers JSON endpoint (more reliable)
        tickers_url = "https://www.sec.gov/files/company_tickers.json"
        resp = requests.get(tickers_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                cik = str(entry["cik_str"]).zfill(10)
                logger.info(f"Found CIK for {ticker}: {cik}")
                return cik

    except Exception as e:
        logger.error(f"CIK lookup failed: {e}")

    return ""


def _get_latest_filing_url(cik: str, filing_type: str) -> str:
    """Get URL of the latest filing of given type."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    try:
        time.sleep(0.15)  # Rate limit: 10 req/sec
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])

        for i, form in enumerate(forms):
            if form == filing_type:
                accession = accessions[i].replace("-", "")
                doc = primary_docs[i]
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession}/{doc}"
                logger.info(f"Found {filing_type} filing: {filing_url}")
                return filing_url

    except Exception as e:
        logger.error(f"Filing URL lookup failed: {e}")

    return ""


def _download_and_parse(url: str) -> str:
    """Download filing and extract plain text."""
    try:
        time.sleep(0.15)  # Rate limit
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")

        if "html" in content_type or url.endswith(".htm") or url.endswith(".html"):
            # Parse HTML filing
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style tags
            for tag in soup(["script", "style", "meta", "link"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
        else:
            # Plain text filing
            text = response.text

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)

        return text

    except Exception as e:
        logger.error(f"Filing download/parse failed: {e}")
        return ""


def get_filing_summary(ticker: str) -> dict:
    """
    Get a summary of available filings for a ticker.

    Returns:
        Dict with filing_type, date, and URL for recent filings
    """
    try:
        cik = _get_cik(ticker)
        if not cik:
            return {"error": f"CIK not found for {ticker}"}

        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        time.sleep(0.15)
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])

        # Get unique recent filing types
        filings = []
        seen = set()
        for i, form in enumerate(forms):
            if form in ("10-K", "10-Q", "8-K") and form not in seen:
                seen.add(form)
                filings.append({
                    "type": form,
                    "date": dates[i] if i < len(dates) else "N/A",
                })

        return {
            "company": data.get("name", ticker),
            "cik": cik,
            "recent_filings": filings,
        }

    except Exception as e:
        logger.error(f"Filing summary failed: {e}")
        return {"error": str(e)}
