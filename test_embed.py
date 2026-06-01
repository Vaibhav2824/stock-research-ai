"""Test just embedder + LLM."""
import os
os.environ['LOG_LEVEL'] = 'INFO'

print("Step 1: Testing embedder...")
try:
    from rag.embedder import embed_texts
    vecs = embed_texts(["Apple reported strong earnings", "Revenue grew 15%"])
    print(f"  OK: shape={vecs.shape}, dtype={vecs.dtype}")
except Exception as e:
    print(f"  FAIL: {type(e).__name__}: {e}")

print("Step 2: Testing LLM...")
try:
    from config import get_llm_response
    resp = get_llm_response("Reply with exactly: OK", temperature=0.1)
    print(f"  OK: {resp.strip()[:50]}")
except Exception as e:
    print(f"  FAIL: {type(e).__name__}: {e}")

print("Step 3: Testing EDGAR...")
try:
    from tools.edgar_tool import download_filing
    text = download_filing("AAPL", filing_type="10-K")
    print(f"  OK: {len(text)} chars")
except Exception as e:
    print(f"  FAIL: {type(e).__name__}: {e}")

print("DONE")
