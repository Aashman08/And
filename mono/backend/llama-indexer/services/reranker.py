"""Reranking service using Cohere Rerank API v3."""
import logging
from typing import List, Tuple

import httpx

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

logger = logging.getLogger(__name__)

COHERE_RERANK_URL = "https://api.cohere.ai/v1/rerank"


async def rerank_documents(
    query: str,
    documents: List[dict],
    top_n: int = 30,
) -> List[Tuple[dict, float]]:
    """
    Rerank documents using Cohere Rerank v3 API.

    Args:
        query: Search query
        documents: List of document dictionaries with 'text' field
        top_n: Number of top results to return

    Returns:
        List of (document, rerank_score) tuples, sorted by score descending
    """
    if not documents:
        return []

    # Prepare documents for reranking
    # Extract text from documents (use title + snippet)
    texts = []
    for doc in documents:
        text = f"{doc.get('title', '')} {doc.get('snippet', '')}".strip()
        texts.append(text)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                COHERE_RERANK_URL,
                json={
                    "model": "rerank-english-v3.0",
                    "query": query,
                    "documents": texts,
                    "top_n": min(top_n, len(texts)),
                    "return_documents": False,
                },
                headers={
                    "Authorization": f"Bearer {settings.cohere_api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            result = response.json()

        # Parse results
        reranked = []
        for item in result.get("results", []):
            index = item["index"]
            score = item["relevance_score"]
            reranked.append((documents[index], score))

        logger.info(f"Reranked {len(documents)} documents to top {len(reranked)}")
        return reranked

    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        # Fallback: return original documents with their scores
        logger.warning("Falling back to original ranking")
        return [(doc, doc.get("score", 0.0)) for doc in documents[:top_n]]

