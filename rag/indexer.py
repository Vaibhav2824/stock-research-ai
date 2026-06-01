"""
TradeMind — FAISS Indexer
Chunks text, embeds it, builds a FAISS index, and persists to disk.
"""

import logging
import os
import pickle
import faiss
import numpy as np

from rag.embedder import embed_texts

logger = logging.getLogger("trademind.rag.indexer")

# Cache directory for persisted indexes
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks by word count.

    Args:
        text: Raw text to split
        chunk_size: Target words per chunk
        overlap: Overlap words between chunks

    Returns:
        List of text chunks
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap

    logger.info(f"Split text into {len(chunks)} chunks (chunk_size={chunk_size}, overlap={overlap})")
    return chunks


def build_index(text: str, ticker: str, force_rebuild: bool = False) -> tuple:
    """
    Build a FAISS index from text content.

    Args:
        text: Raw text to index (e.g., SEC filing content)
        ticker: Stock symbol (used for cache key)
        force_rebuild: If True, rebuild even if cached

    Returns:
        Tuple of (faiss_index, chunks_list)
    """
    cache_index_path = os.path.join(CACHE_DIR, f"{ticker.upper()}_index.faiss")
    cache_chunks_path = os.path.join(CACHE_DIR, f"{ticker.upper()}_chunks.pkl")

    # Check cache
    if not force_rebuild and os.path.exists(cache_index_path) and os.path.exists(cache_chunks_path):
        logger.info(f"Loading cached FAISS index for {ticker}")
        index = faiss.read_index(cache_index_path)
        with open(cache_chunks_path, "rb") as f:
            chunks = pickle.load(f)
        logger.info(f"Loaded {index.ntotal} vectors from cache")
        return index, chunks

    # Chunk the text
    chunks = chunk_text(text)
    if not chunks:
        logger.warning(f"No chunks generated for {ticker}")
        return None, []

    # Embed chunks
    embeddings = embed_texts(chunks)
    if embeddings.size == 0:
        logger.warning(f"No embeddings generated for {ticker}")
        return None, []

    # Build FAISS index (Inner Product for normalized vectors = cosine similarity)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Save to disk
    faiss.write_index(index, cache_index_path)
    with open(cache_chunks_path, "wb") as f:
        pickle.dump(chunks, f)

    logger.info(f"Built FAISS index for {ticker}: {index.ntotal} vectors, dim={dimension}")
    return index, chunks


def index_exists(ticker: str) -> bool:
    """Check if a cached index exists for a ticker."""
    cache_index_path = os.path.join(CACHE_DIR, f"{ticker.upper()}_index.faiss")
    cache_chunks_path = os.path.join(CACHE_DIR, f"{ticker.upper()}_chunks.pkl")
    return os.path.exists(cache_index_path) and os.path.exists(cache_chunks_path)
