"""Quick LLM + Embedding test using new google-genai SDK."""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY", "")
print(f"API Key: {api_key[:10]}... ({len(api_key)} chars)")

from google import genai
client = genai.Client(api_key=api_key)

print("\n1. Testing LLM (gemini-2.0-flash)...")
try:
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Reply with exactly: LLM_OK",
    )
    print(f"   SUCCESS: {resp.text.strip()}")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")

time.sleep(3)

print("\n2. Testing Embedding (gemini-embedding-001)...")
try:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=["Apple earnings beat expectations", "Revenue grew 15%"],
    )
    print(f"   SUCCESS: {len(result.embeddings)} embeddings, dim={len(result.embeddings[0].values)}")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")

print("\nAll tests done.")
