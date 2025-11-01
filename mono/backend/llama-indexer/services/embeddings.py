"""Embedding service using sentence-transformers e5-base-v2."""
import logging
from typing import List, Union

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Get or initialize the embedding model."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded successfully")
    return _model


def embed_query(query: str) -> np.ndarray:
    """
    Embed a search query with the 'query: ' prefix.

    Args:
        query: The search query string

    Returns:
        Embedding vector as numpy array
    """
    model = get_model()
    prefixed_query = f"query: {query}"
    embedding = model.encode(prefixed_query, convert_to_numpy=True, normalize_embeddings=True)
    return embedding


def embed_passages(passages: List[str]) -> np.ndarray:
    """
    Embed passages/chunks with the 'passage: ' prefix.

    Args:
        passages: List of text passages to embed

    Returns:
        Array of embedding vectors (shape: [n_passages, embedding_dim])
    """
    model = get_model()
    prefixed_passages = [f"passage: {p}" for p in passages]
    embeddings = model.encode(
        prefixed_passages,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=len(passages) > 100,
    )
    return embeddings


def cosine_similarity(
    query_embedding: np.ndarray,
    passage_embeddings: Union[np.ndarray, List[np.ndarray]],
) -> np.ndarray:
    """
    Compute cosine similarity between query and passages.

    Assumes embeddings are already normalized.

    Args:
        query_embedding: Query vector (1D)
        passage_embeddings: Passage vectors (2D or list of 1D)

    Returns:
        Array of similarity scores
    """
    if isinstance(passage_embeddings, list):
        passage_embeddings = np.array(passage_embeddings)

    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    if passage_embeddings.ndim == 1:
        passage_embeddings = passage_embeddings.reshape(1, -1)

    # Dot product for normalized vectors = cosine similarity
    similarities = np.dot(passage_embeddings, query_embedding.T).flatten()
    return similarities


def get_embedding_dimension() -> int:
    """Get the dimensionality of the embedding model."""
    model = get_model()
    return model.get_sentence_embedding_dimension()
