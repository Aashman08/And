"""Highlight service for generating why_this_result explanations."""
import logging
import re
from typing import List

import numpy as np

from app.services.embeddings import embed_query, cosine_similarity

logger = logging.getLogger(__name__)

MAX_HIGHLIGHTS = 3


def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Simple sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]


def generate_highlights(
    query: str,
    document_text: str,
    max_highlights: int = MAX_HIGHLIGHTS,
) -> List[str]:
    """
    Generate highlight sentences that explain why this document is relevant.

    Selects top N sentences with highest cosine similarity to query embedding.

    Args:
        query: Search query
        document_text: Document content (abstract/description)
        max_highlights: Maximum number of highlights to return

    Returns:
        List of highlight sentences
    """
    try:
        # Extract sentences
        sentences = extract_sentences(document_text)

        if not sentences:
            return []

        # Embed query
        query_embedding = embed_query(query)

        # Embed sentences (without passage prefix for this use case)
        from app.services.embeddings import get_model
        model = get_model()
        sentence_embeddings = model.encode(
            sentences,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        # Compute similarities
        similarities = cosine_similarity(query_embedding, sentence_embeddings)

        # Get top N sentences
        top_indices = np.argsort(similarities)[::-1][:max_highlights]

        highlights = [sentences[i] for i in top_indices]

        return highlights

    except Exception as e:
        logger.error(f"Failed to generate highlights: {e}")
        # Fallback: return first few sentences
        sentences = extract_sentences(document_text)
        return sentences[:max_highlights]


def generate_highlights_batch(
    query: str,
    documents: List[dict],
) -> List[List[str]]:
    """
    Generate highlights for multiple documents.

    Args:
        query: Search query
        documents: List of document dictionaries with 'snippet' or 'description' field

    Returns:
        List of highlight lists, one per document
    """
    highlights_batch = []

    for doc in documents:
        text = doc.get("snippet", doc.get("description", ""))
        highlights = generate_highlights(query, text)
        highlights_batch.append(highlights)

    return highlights_batch
