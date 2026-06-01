"""
TradeMind — Embedder
Uses Google Generative AI embeddings (free) as primary,
with a fallback to a simple TF-IDF based approach.
Avoids torch/sentence-transformers which crash on Python 3.14.
"""

import logging
import numpy as np
import os

logger = logging.getLogger("trademind.rag.embedder")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Embedding dimension for gemini-embedding-001
EMBEDDING_DIM = 3072


def embed_texts(texts: list[str], batch_size: int = 20) -> np.ndarray:
    """
    Embed a list of text chunks into dense vectors.

    Args:
        texts: List of text strings to embed
        batch_size: Batch size for API calls

    Returns:
        numpy array of shape (n_texts, dim)
    """
    if not texts:
        return np.array([]).reshape(0, EMBEDDING_DIM).astype(np.float32)

    # Try Gemini embeddings first
    if GEMINI_API_KEY:
        try:
            return _embed_gemini(texts, batch_size)
        except Exception as e:
            logger.warning(f"Gemini embedding failed: {e}. Falling back to TF-IDF.")

    # Fallback: TF-IDF based embeddings (no external deps)
    return _embed_tfidf(texts)


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.

    Args:
        query: Search query

    Returns:
        numpy array of shape (1, dim)
    """
    return embed_texts([query])


def _embed_gemini(texts: list[str], batch_size: int = 100) -> np.ndarray:
    """Embed using Google's free embedding API (new google-genai SDK)."""
    import time
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        # Truncate long texts to avoid token limits
        batch = [t[:2000] for t in batch]

        logger.info(f"Embedding batch {i // batch_size + 1} ({len(batch)} texts)...")

        for attempt in range(3):
            try:
                result = client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=batch,
                )
                for emb in result.embeddings:
                    all_embeddings.append(emb.values)
                break
            except Exception as e:
                error_str = str(e).lower()
                if any(kw in error_str for kw in ["quota", "rate", "429", "resource"]):
                    wait_time = 10 * (attempt + 1)
                    logger.warning(f"Embedding quota hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

    embeddings = np.array(all_embeddings, dtype=np.float32)

    # Normalize for cosine similarity via dot product
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    embeddings = embeddings / norms

    logger.info(f"Embedded {len(texts)} chunks via Gemini → shape {embeddings.shape}")
    return embeddings


def _embed_tfidf(texts: list[str]) -> np.ndarray:
    """
    Fallback: Simple TF-IDF style embeddings using hashing.
    Not as good as neural embeddings, but works without any ML libs.
    """
    import hashlib
    from collections import Counter

    logger.info(f"Using TF-IDF fallback for {len(texts)} texts...")

    dim = EMBEDDING_DIM
    embeddings = []

    # Build document frequency
    all_words = set()
    doc_words = []
    for text in texts:
        words = _tokenize(text)
        doc_words.append(words)
        all_words.update(set(words))

    for words in doc_words:
        vec = np.zeros(dim, dtype=np.float32)
        word_counts = Counter(words)
        for word, count in word_counts.items():
            # Hash word to a dimension index
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % dim
            tf = count / len(words) if words else 0
            vec[idx] += tf

        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        embeddings.append(vec)

    result = np.array(embeddings, dtype=np.float32)
    logger.info(f"TF-IDF embedded {len(texts)} chunks → shape {result.shape}")
    return result


def _tokenize(text: str) -> list[str]:
    """Simple word tokenizer."""
    import re
    text = text.lower()
    words = re.findall(r'\b[a-z]{2,}\b', text)
    # Remove common stop words
    stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
                  'in', 'with', 'to', 'for', 'of', 'not', 'no', 'can', 'had', 'has',
                  'have', 'do', 'did', 'be', 'been', 'being', 'this', 'that', 'it',
                  'its', 'as', 'are', 'was', 'were', 'from', 'by', 'will', 'would',
                  'could', 'should', 'may', 'might', 'shall', 'so', 'if', 'then',
                  'than', 'too', 'very', 'just', 'about', 'also', 'other', 'into',
                  'more', 'some', 'such', 'only', 'over', 'any', 'each', 'all'}
    return [w for w in words if w not in stop_words]
