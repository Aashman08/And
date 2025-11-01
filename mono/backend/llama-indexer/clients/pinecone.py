"""Pinecone client for vector similarity search."""
import logging
from typing import List, Dict, Any
import time

from pinecone import Pinecone, ServerlessSpec

from app.config import settings
from app.services.embeddings import get_embedding_dimension

logger = logging.getLogger(__name__)

# Global Pinecone instance
_pc: Pinecone | None = None
_index = None


def get_pinecone() -> Pinecone:
    """Get or create Pinecone client."""
    global _pc
    if _pc is None:
        _pc = Pinecone(api_key=settings.pinecone_api_key)
        logger.info("Initialized Pinecone client")
    return _pc


def get_index():
    """Get or create Pinecone index."""
    global _index
    if _index is None:
        pc = get_pinecone()
        _index = pc.Index(settings.pinecone_index_name)
        logger.info(f"Connected to Pinecone index: {settings.pinecone_index_name}")
    return _index


def create_index():
    """Create Pinecone serverless index if it doesn't exist."""
    pc = get_pinecone()
    index_name = settings.pinecone_index_name

    # Check if index exists
    existing_indexes = pc.list_indexes()
    index_exists = any(idx.name == index_name for idx in existing_indexes)

    if index_exists:
        logger.info(f"Index {index_name} already exists")
        return

    # Get embedding dimension
    dimension = get_embedding_dimension()
    logger.info(f"Creating Pinecone index with dimension {dimension}")

    # Create serverless index
    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_environment,
        ),
    )

    # Wait for index to be ready
    while not pc.describe_index(index_name).status.ready:
        logger.info("Waiting for index to be ready...")
        time.sleep(1)

    logger.info(f"Created Pinecone index: {index_name}")


def upsert_vectors_bulk(vectors: List[Dict[str, Any]], batch_size: int = 100):
    """
    Bulk upsert vectors to Pinecone.

    Args:
        vectors: List of vector dictionaries with id, values, metadata
        batch_size: Batch size for upserts

    Returns:
        Number of vectors upserted
    """
    index = get_index()
    total_upserted = 0

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]

        # Format for Pinecone
        formatted_batch = [
            (v["id"], v["values"], v.get("metadata", {}))
            for v in batch
        ]

        index.upsert(vectors=formatted_batch)
        total_upserted += len(batch)

        if i % 500 == 0 and i > 0:
            logger.info(f"Upserted {total_upserted} vectors so far...")

    logger.info(f"Total vectors upserted: {total_upserted}")
    return total_upserted


def search_vectors(
    query_vector: List[float],
    top_k: int = 200,
    filter_dict: Dict[str, Any] | None = None,
) -> List[dict]:
    """
    Search for similar vectors in Pinecone.

    Args:
        query_vector: Query embedding vector
        top_k: Number of results to return
        filter_dict: Optional metadata filters

    Returns:
        List of search results with scores and metadata
    """
    index = get_index()

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict,
    )

    return [
        {
            "chunk_id": match.id,
            "doc_id": match.metadata.get("doc_id"),
            "score": match.score,
            "title": match.metadata.get("title", ""),
            "snippet": match.metadata.get("text", "")[:300],
            "source": match.metadata.get("source"),
            "metadata": {
                "year": match.metadata.get("year"),
                "section": match.metadata.get("section"),
            },
        }
        for match in results.matches
    ]


def delete_all_vectors():
    """Delete all vectors from the index (for testing/reset)."""
    index = get_index()
    index.delete(delete_all=True)
    logger.warning("Deleted all vectors from Pinecone index")


def get_index_stats() -> dict:
    """Get statistics about the index."""
    index = get_index()
    stats = index.describe_index_stats()
    return {
        "total_vectors": stats.total_vector_count,
        "dimension": stats.dimension,
    }
