"""
TradeMind — yfinance Tool
Fetches stock OHLCV data, company info, and financials via yfinance.
"""

import logging
import yfinance as yf
import pandas as pd

logger = logging.getLogger("trademind.tools.yfinance")


def get_stock_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """
    Fetch OHLCV data for a ticker.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        period: Data period — 1mo, 3mo, 6mo, 1y, 2y, 5y

    Returns:
        DataFrame with Date, Open, High, Low, Close, Volume columns
    """
    logger.info(f"Fetching OHLCV data for {ticker} (period={period})")
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            logger.warning(f"No data returned for {ticker}")
            return pd.DataFrame()

        # Clean up columns
        df = df.reset_index()
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        logger.info(f"Got {len(df)} rows of OHLCV data for {ticker}")
        return df

    except Exception as e:
        logger.error(f"Failed to fetch stock data for {ticker}: {e}")
        return pd.DataFrame()


def get_company_info(ticker: str) -> dict:
    """
    Fetch company metadata: name, sector, market cap, etc.

    Returns:
        Dict with keys: name, sector, industry, market_cap, pe_ratio,
        forward_pe, dividend_yield, 52w_high, 52w_low, avg_volume, description
    """
    logger.info(f"Fetching company info for {ticker}")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        result = {
            "name": info.get("longName", info.get("shortName", ticker)),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "forward_pe": info.get("forwardPE", None),
            "dividend_yield": info.get("dividendYield", None),
            "52w_high": info.get("fiftyTwoWeekHigh", None),
            "52w_low": info.get("fiftyTwoWeekLow", None),
            "avg_volume": info.get("averageVolume", 0),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", None)),
            "description": info.get("longBusinessSummary", ""),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", ""),
        }

        logger.info(f"Company info for {ticker}: {result['name']} ({result['sector']})")
        return result

    except Exception as e:
        logger.error(f"Failed to fetch company info for {ticker}: {e}")
        return {"name": ticker, "sector": "N/A", "error": str(e)}


def get_financials(ticker: str) -> dict:
    """
    Fetch financial statements: income statement, balance sheet.

    Returns:
        Dict with 'income_statement' and 'balance_sheet' DataFrames as dicts
    """
    logger.info(f"Fetching financials for {ticker}")
    try:
        stock = yf.Ticker(ticker)

        income = stock.financials
        balance = stock.balance_sheet

        result = {
            "income_statement": income.to_dict() if not income.empty else {},
            "balance_sheet": balance.to_dict() if not balance.empty else {},
            "revenue": _extract_metric(income, "Total Revenue"),
            "net_income": _extract_metric(income, "Net Income"),
            "total_debt": _extract_metric(balance, "Total Debt"),
            "total_equity": _extract_metric(balance, "Total Stockholder Equity",
                                            fallback_key="Stockholders Equity"),
            "cash": _extract_metric(balance, "Cash And Cash Equivalents",
                                    fallback_key="Cash"),
        }

        logger.info(f"Financials fetched for {ticker}")
        return result

    except Exception as e:
        logger.error(f"Failed to fetch financials for {ticker}: {e}")
        return {"error": str(e)}


def _extract_metric(df: pd.DataFrame, key: str, fallback_key: str = None) -> list:
    """Extract a row from financial DataFrame as a list of (date, value) pairs."""
    if df.empty:
        return []

    for k in [key, fallback_key]:
        if k and k in df.index:
            row = df.loc[k]
            return [
                {"date": str(col.date()) if hasattr(col, "date") else str(col),
                 "value": float(val) if pd.notna(val) else None}
                for col, val in row.items()
            ]
    return []


def validate_ticker(ticker: str) -> bool:
    """Check if a ticker symbol is valid by attempting to fetch its info."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # yfinance returns a dict even for invalid tickers, but key fields will be missing
        return bool(info.get("longName") or info.get("shortName"))
    except Exception:
        return False
