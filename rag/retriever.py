"""
TradeMind — RAG Retriever
Queries a FAISS index to retrieve the most relevant text chunks.
"""

import logging
import os
import pickle
import faiss

from rag.embedder import embed_query

logger = logging.getLogger("trademind.rag.retriever")

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")


def retrieve(query: str, ticker: str, top_k: int = 5) -> list[str]:
    """
    Retrieve the top-k most relevant chunks for a query.

    Args:
        query: Natural language query (e.g., "revenue growth trend")
        ticker: Stock symbol (to load the correct index)
        top_k: Number of chunks to retrieve

    Returns:
        List of text chunks, ordered by relevance (most relevant first)
    """
    cache_index_path = os.path.join(CACHE_DIR, f"{ticker.upper()}_index.faiss")
    cache_chunks_path = os.path.join(CACHE_DIR, f"{ticker.upper()}_chunks.pkl")

    if not os.path.exists(cache_index_path) or not os.path.exists(cache_chunks_path):
        logger.warning(f"No FAISS index found for {ticker}. Run indexer first.")
        return []

    # Load index and chunks
    index = faiss.read_index(cache_index_path)
    with open(cache_chunks_path, "rb") as f:
        chunks = pickle.load(f)

    # Embed the query
    query_vec = embed_query(query)

    # Search
    k = min(top_k, index.ntotal)
    distances, indices = index.search(query_vec, k)

    # Collect results
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks) and idx >= 0:
            results.append(chunks[idx])
            logger.debug(f"  Chunk {i+1}: score={distances[0][i]:.4f}, len={len(chunks[idx])}")

    logger.info(f"Retrieved {len(results)} chunks for query: '{query[:50]}...'")
    return results


def multi_query_retrieve(queries: list[str], ticker: str, top_k: int = 5) -> list[str]:
    """
    Run multiple queries and merge unique results.

    Args:
        queries: List of queries to run
        ticker: Stock symbol
        top_k: Chunks per query

    Returns:
        Deduplicated list of relevant chunks
    """
    all_chunks = []
    seen = set()

    for query in queries:
        chunks = retrieve(query, ticker, top_k=top_k)
        for chunk in chunks:
            chunk_key = chunk[:100]  # Use first 100 chars as dedup key
            if chunk_key not in seen:
                seen.add(chunk_key)
                all_chunks.append(chunk)

    logger.info(f"Multi-query retrieved {len(all_chunks)} unique chunks from {len(queries)} queries")
    return all_chunks
