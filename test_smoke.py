"""Quick smoke test of all TradeMind tools."""
import os
os.environ['LOG_LEVEL'] = 'WARNING'

from tools.yfinance_tool import get_company_info, get_stock_data
from tools.ta_tool import compute_indicators
from tools.news_tool import fetch_news

print("=== Testing Tools ===")

info = get_company_info("AAPL")
print(f"Company: {info.get('name', 'ERROR')} | Price: ${info.get('current_price', 'N/A')}")

df = get_stock_data("AAPL", period="6mo")
print(f"OHLCV: {len(df)} rows")

ta = compute_indicators(df)
print(f"RSI: {ta.get('rsi',{}).get('value')} | MACD: {ta.get('macd',{}).get('signal')} | Overall: {ta.get('overall_signal')}")

news = fetch_news("AAPL", company_name="Apple Inc", days=14)
print(f"News articles: {len(news)}")

print("\n=== Testing Embedder ===")
from rag.embedder import embed_texts
vecs = embed_texts(["Apple reported strong earnings", "Revenue grew 15% year over year"])
print(f"Embeddings shape: {vecs.shape}")

print("\n=== Testing LLM ===")
from config import get_llm_response
resp = get_llm_response("Say 'TradeMind works!' in exactly 3 words.", temperature=0.1)
print(f"LLM response: {resp.strip()}")

print("\n=== ALL TESTS PASSED ===")
