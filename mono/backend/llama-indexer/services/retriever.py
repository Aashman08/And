"""Hybrid retrieval service combining BM25 and vector search."""
import logging
from typing import List, Dict, Any

import numpy as np

from app.clients import opensearch, pinecone
from app.services.embeddings import embed_query

# Alias for compatibility
opensearch_client = opensearch
pinecone_client = pinecone

logger = logging.getLogger(__name__)

# Hybrid blending weights
BM25_WEIGHT = 0.6
ANN_WEIGHT = 0.4

BM25_TOP_K = 200
ANN_TOP_K = 200


def normalize_scores(results: List[dict], score_key: str = "score") -> List[dict]:
    """
    Min-max normalize scores in results list.

    Args:
        results: List of result dictionaries
        score_key: Key containing the score

    Returns:
        Results with normalized scores
    """
    if not results:
        return results

    scores = [r[score_key] for r in results]
    min_score = min(scores)
    max_score = max(scores)

    # Avoid division by zero
    if max_score == min_score:
        for r in results:
            r[f"{score_key}_norm"] = 1.0
        return results

    for r in results:
        r[f"{score_key}_norm"] = (r[score_key] - min_score) / (max_score - min_score)

    return results


def dedupe_and_blend(
    bm25_results: List[dict],
    ann_results: List[dict],
) -> List[dict]:
    """
    Deduplicate and blend BM25 and ANN results.

    Combines scores using weighted average: 0.6 * BM25 + 0.4 * ANN

    Args:
        bm25_results: BM25 search results
        ann_results: Vector search results

    Returns:
        Blended and deduplicated results sorted by score
    """
    # Normalize scores
    bm25_results = normalize_scores(bm25_results)
    ann_results = normalize_scores(ann_results)

    # Build doc_id -> result mapping
    doc_scores: Dict[str, dict] = {}

    # Add BM25 results
    for result in bm25_results:
        doc_id = result["doc_id"]
        doc_scores[doc_id] = {
            **result,
            "bm25_score": result["score_norm"],
            "ann_score": 0.0,
            "sources": ["bm25"],
        }

    # Merge ANN results
    for result in ann_results:
        doc_id = result["doc_id"]
        if doc_id in doc_scores:
            doc_scores[doc_id]["ann_score"] = result["score_norm"]
            doc_scores[doc_id]["sources"].append("ann")
        else:
            doc_scores[doc_id] = {
                **result,
                "bm25_score": 0.0,
                "ann_score": result["score_norm"],
                "sources": ["ann"],
            }

    # Calculate hybrid scores
    for doc_id, result in doc_scores.items():
        hybrid_score = (
            BM25_WEIGHT * result["bm25_score"] +
            ANN_WEIGHT * result["ann_score"]
        )
        result["score"] = hybrid_score

    # Sort by hybrid score (descending), then by year (newer first)
    blended_results = sorted(
        doc_scores.values(),
        key=lambda x: (x["score"], x.get("metadata", {}).get("year", 0)),
        reverse=True,
    )

    logger.info(
        f"Blended {len(bm25_results)} BM25 + {len(ann_results)} ANN "
        f"results into {len(blended_results)} unique documents"
    )

    return blended_results


async def hybrid_search(
    query: str,
    source_filter: List[str] | None = None,
    year_gte: int | None = None,
    top_k: int = 256,
) -> List[dict]:
    """
    Perform hybrid search combining BM25 and vector search.

    Args:
        query: Search query
        source_filter: Filter by source types (papers/startups)
        year_gte: Filter by minimum year
        top_k: Number of results to return after blending

    Returns:
        List of search results with hybrid scores
    """
    logger.info(f"Hybrid search for query: {query}")

    # Embed query for vector search
    query_embedding = embed_query(query)

    bm25_results = []
    ann_results = []

    # Determine which sources to search
    search_papers = not source_filter or "papers" in source_filter
    search_startups = not source_filter or "startups" in source_filter

    # BM25 search
    if search_papers:
        try:
            papers_bm25 = opensearch_client.search_papers(
                query, top_k=BM25_TOP_K, year_gte=year_gte
            )
            for result in papers_bm25:
                result["source"] = "papers"
            bm25_results.extend(papers_bm25)
        except Exception as e:
            logger.error(f"BM25 papers search failed: {e}")

    if search_startups:
        try:
            startups_bm25 = opensearch_client.search_startups(
                query, top_k=BM25_TOP_K, year_gte=year_gte
            )
            for result in startups_bm25:
                result["source"] = "startups"
            bm25_results.extend(startups_bm25)
        except Exception as e:
            logger.error(f"BM25 startups search failed: {e}")

    # Vector search in Pinecone
    try:
        # Build filter for Pinecone
        pinecone_filter = {}
        if source_filter:
            pinecone_filter["source"] = {"$in": source_filter}
        if year_gte:
            pinecone_filter["year"] = {"$gte": year_gte}

        ann_results = pinecone_client.search_vectors(
            query_vector=query_embedding.tolist(),
            top_k=ANN_TOP_K,
            filter_dict=pinecone_filter if pinecone_filter else None,
        )
    except Exception as e:
        logger.error(f"Vector search failed: {e}")

    # Blend results
    blended = dedupe_and_blend(bm25_results, ann_results)

    return blended[:top_k]
