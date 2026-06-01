"""
TradeMind MVP — Configuration & LLM Client Factory
Loads environment variables and provides a unified LLM interface.
"""

import os
import logging
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(override=True)

# ============================================
# Logging
# ============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("trademind")

# ============================================
# API Keys
# ============================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
EDGAR_USER_AGENT = os.getenv("EDGAR_USER_AGENT", "TradeMind research@trademind.dev")

# ============================================
# LLM Settings
# ============================================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" | "groq" | "openrouter"
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-lite-preview-02-05:free")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4096))  # Must be large enough to not clip JSON

# ============================================
# LLM Client Factory
# ============================================

def get_llm_response(prompt: str, system_prompt: str = "", temperature: float = 0.3) -> str:
    """
    Unified LLM call. Tries primary provider, falls back to secondary.
    Returns raw text response.
    """
    providers = _get_provider_chain()

    last_error = None
    for provider_fn in providers:
        try:
            return provider_fn(prompt, system_prompt, temperature)
        except Exception as e:
            last_error = e
            logger.warning(f"LLM provider failed: {e}. Trying next...")

    raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")


def _get_provider_chain():
    """Returns ordered list of LLM provider functions based on config."""
    chain = []

    if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        chain.append(_call_gemini)
    if GROQ_API_KEY:
        chain.append(_call_groq)
    if OPENROUTER_API_KEY:
        chain.append(_call_openrouter)
    if LLM_PROVIDER != "gemini" and GEMINI_API_KEY:
        chain.append(_call_gemini)

    if not chain:
        raise RuntimeError(
            "No LLM provider configured. Set GEMINI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY in .env"
        )
    return chain


def _call_gemini(prompt: str, system_prompt: str, temperature: float) -> str:
    """Call Google Gemini API using the new google-genai SDK."""
    import time
    from google import genai
    from google.genai import types

    # THROTTLE: Google Free Tier is 15 RPM. 
    # Waiting 4.1 seconds guarantees max ~14.6 RPM, completely eliminating the 429 quota error.
    time.sleep(4.1)

    client = genai.Client(api_key=GEMINI_API_KEY)
    model_name = "gemini-2.0-flash"

    # Build config
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=MAX_TOKENS,
    )
    if system_prompt:
        config.system_instruction = system_prompt

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        return response.text
    except Exception as e:
        logger.warning(f"Gemini API failed instantly: {e}")
        raise


def _call_groq(prompt: str, system_prompt: str, temperature: float) -> str:
    """Call Groq API (Llama 3 — fast + free)."""
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=temperature,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content

def _call_openrouter(prompt: str, system_prompt: str, temperature: float) -> str:
    """Call OpenRouter API with multiple free fallbacks to guarantee uptime."""
    import requests
    import json

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501", # Required by OpenRouter
        "X-Title": "TradeMind", # Required by OpenRouter
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    fallback_models = [
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "huggingfaceh4/zephyr-7b-beta:free",
        "mistralai/mistral-nemo:free"
    ]

    last_error = ""
    for model_name in fallback_models:
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": MAX_TOKENS,
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                resp_json = response.json()
                return resp_json["choices"][0]["message"]["content"]
            else:
                last_error = f"{response.status_code}: {response.text}"
                logger.warning(f"OpenRouter model {model_name} failed: {last_error}")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"OpenRouter model {model_name} raised error: {last_error}")

    raise RuntimeError(f"All OpenRouter fallback models failed. Last error: {last_error}")


# ============================================
# Cache Settings
# ============================================
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
