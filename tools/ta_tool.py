"""
TradeMind — Technical Analysis Tool
Computes RSI, MACD, Bollinger Bands, SMA, and volatility using the `ta` library.
"""

import logging
import pandas as pd
import numpy as np
import ta as ta_lib

logger = logging.getLogger("trademind.tools.ta")


def compute_indicators(df: pd.DataFrame) -> dict:
    """
    Compute all technical indicators from OHLCV data.

    Args:
        df: DataFrame with 'close', 'high', 'low', 'volume' columns

    Returns:
        Dict with all computed indicators and their latest values
    """
    logger.info("Computing technical indicators...")

    if df.empty or len(df) < 30:
        logger.warning("Insufficient data for technical analysis")
        return {"error": "Insufficient data (need at least 30 days)"}

    # Ensure column names are lowercase
    df.columns = [c.lower() for c in df.columns]

    result = {}

    # --- RSI (14-period) ---
    try:
        rsi_series = ta_lib.momentum.RSIIndicator(close=df["close"], window=14).rsi()
        rsi_val = rsi_series.iloc[-1]
        result["rsi"] = {
            "value": round(float(rsi_val), 2) if pd.notna(rsi_val) else None,
            "signal": _rsi_signal(rsi_val),
            "history": [round(float(v), 2) if pd.notna(v) else None for v in rsi_series.tail(30)],
        }
    except Exception as e:
        logger.error(f"RSI computation failed: {e}")
        result["rsi"] = {"value": None, "signal": "N/A", "error": str(e)}

    # --- MACD (12, 26, 9) ---
    try:
        macd_ind = ta_lib.trend.MACD(close=df["close"], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd_ind.macd()
        signal_line = macd_ind.macd_signal()
        histogram = macd_ind.macd_diff()

        result["macd"] = {
            "macd_line": round(float(macd_line.iloc[-1]), 4) if pd.notna(macd_line.iloc[-1]) else None,
            "signal_line": round(float(signal_line.iloc[-1]), 4) if pd.notna(signal_line.iloc[-1]) else None,
            "histogram": round(float(histogram.iloc[-1]), 4) if pd.notna(histogram.iloc[-1]) else None,
            "signal": _macd_signal(macd_line.iloc[-1], signal_line.iloc[-1]),
            "macd_history": [round(float(v), 4) if pd.notna(v) else None for v in macd_line.tail(30)],
            "signal_history": [round(float(v), 4) if pd.notna(v) else None for v in signal_line.tail(30)],
        }
    except Exception as e:
        logger.error(f"MACD computation failed: {e}")
        result["macd"] = {"macd_line": None, "signal": "N/A", "error": str(e)}

    # --- Bollinger Bands (20, 2) ---
    try:
        bb = ta_lib.volatility.BollingerBands(close=df["close"], window=20, window_dev=2)
        upper = bb.bollinger_hband().iloc[-1]
        middle = bb.bollinger_mavg().iloc[-1]
        lower = bb.bollinger_lband().iloc[-1]

        result["bollinger"] = {
            "upper": round(float(upper), 2) if pd.notna(upper) else None,
            "middle": round(float(middle), 2) if pd.notna(middle) else None,
            "lower": round(float(lower), 2) if pd.notna(lower) else None,
            "current_price": round(float(df["close"].iloc[-1]), 2),
            "signal": _bollinger_signal(df["close"].iloc[-1], upper, lower),
        }
    except Exception as e:
        logger.error(f"Bollinger Bands computation failed: {e}")
        result["bollinger"] = {"upper": None, "signal": "N/A", "error": str(e)}

    # --- SMA (50 and 200) ---
    try:
        sma50_series = ta_lib.trend.SMAIndicator(close=df["close"], window=50).sma_indicator()
        sma50 = sma50_series.iloc[-1]

        if len(df) >= 200:
            sma200_series = ta_lib.trend.SMAIndicator(close=df["close"], window=200).sma_indicator()
            sma200 = sma200_series.iloc[-1]
        else:
            sma200_series = pd.Series([None])
            sma200 = None

        result["sma"] = {
            "sma_50": round(float(sma50), 2) if pd.notna(sma50) else None,
            "sma_200": round(float(sma200), 2) if (sma200 is not None and pd.notna(sma200)) else None,
            "current_price": round(float(df["close"].iloc[-1]), 2),
            "golden_cross": _check_cross(sma50, sma200),
        }
    except Exception as e:
        logger.error(f"SMA computation failed: {e}")
        result["sma"] = {"sma_50": None, "sma_200": None, "error": str(e)}

    # --- Volatility (30-day) ---
    try:
        returns = df["close"].pct_change().dropna()
        vol_30d = float(returns.tail(30).std() * np.sqrt(252) * 100)  # Annualized %
        result["volatility"] = {
            "annualized_30d": round(vol_30d, 2),
            "signal": "High" if vol_30d > 40 else "Medium" if vol_30d > 20 else "Low",
        }
    except Exception as e:
        logger.error(f"Volatility computation failed: {e}")
        result["volatility"] = {"annualized_30d": None, "error": str(e)}

    # --- Price context ---
    result["price"] = {
        "current": round(float(df["close"].iloc[-1]), 2),
        "change_1d": round(float(df["close"].pct_change().iloc[-1] * 100), 2) if len(df) > 1 else 0,
        "change_30d": round(float((df["close"].iloc[-1] / df["close"].iloc[-30] - 1) * 100), 2) if len(df) >= 30 else 0,
        "high_30d": round(float(df["high"].tail(30).max()), 2),
        "low_30d": round(float(df["low"].tail(30).min()), 2),
    }

    # --- Overall trend signal ---
    result["overall_signal"] = _compute_overall_signal(result)

    logger.info(f"Technical analysis complete. Overall signal: {result['overall_signal']}")
    return result


def _rsi_signal(rsi_val) -> str:
    if pd.isna(rsi_val):
        return "N/A"
    if rsi_val > 70:
        return "Overbought"
    elif rsi_val > 60:
        return "Slightly Overbought"
    elif rsi_val < 30:
        return "Oversold"
    elif rsi_val < 40:
        return "Slightly Oversold"
    return "Neutral"


def _macd_signal(macd_val, signal_val) -> str:
    if pd.isna(macd_val) or pd.isna(signal_val):
        return "N/A"
    if macd_val > signal_val:
        return "Bullish"
    return "Bearish"


def _bollinger_signal(price, upper, lower) -> str:
    if pd.isna(upper) or pd.isna(lower):
        return "N/A"
    if price > upper:
        return "Above Upper Band (Overbought)"
    elif price < lower:
        return "Below Lower Band (Oversold)"
    return "Within Bands (Neutral)"


def _check_cross(sma50, sma200) -> str:
    if sma200 is None or pd.isna(sma200) or pd.isna(sma50):
        return "Insufficient data for cross analysis"
    if sma50 > sma200:
        return "Golden Cross (Bullish)"
    else:
        return "Death Cross (Bearish)"


def _compute_overall_signal(indicators: dict) -> str:
    score = 0
    signals = 0

    rsi_val = indicators.get("rsi", {}).get("value")
    if rsi_val is not None:
        if rsi_val > 70: score -= 2
        elif rsi_val > 60: score -= 1
        elif rsi_val < 30: score += 2
        elif rsi_val < 40: score += 1
        signals += 1

    macd_sig = indicators.get("macd", {}).get("signal", "")
    if macd_sig == "Bullish": score += 1
    elif macd_sig == "Bearish": score -= 1
    if macd_sig in ("Bullish", "Bearish"): signals += 1

    bb_sig = indicators.get("bollinger", {}).get("signal", "")
    if "Oversold" in bb_sig: score += 1
    elif "Overbought" in bb_sig: score -= 1
    if bb_sig and bb_sig != "N/A": signals += 1

    cross = indicators.get("sma", {}).get("golden_cross", "")
    if "Golden" in cross: score += 1
    elif "Death" in cross: score -= 1
    if cross and "N/A" not in cross and "Insufficient" not in cross: signals += 1

    if signals == 0: return "N/A"
    avg = score / signals
    if avg >= 1.5: return "Strong Buy"
    elif avg >= 0.5: return "Buy"
    elif avg <= -1.5: return "Strong Sell"
    elif avg <= -0.5: return "Sell"
    return "Hold"
