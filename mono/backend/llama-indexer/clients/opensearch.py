"""OpenSearch client for BM25 full-text search."""
import logging
from typing import List, Dict, Any

from opensearchpy import OpenSearch, helpers
from opensearchpy.exceptions import NotFoundError

from app.config import settings

logger = logging.getLogger(__name__)

PAPERS_INDEX = "papers_bm25"
STARTUPS_INDEX = "startups_bm25"

# Global client instance
_client: OpenSearch | None = None


def get_client() -> OpenSearch:
    """Get or create OpenSearch client."""
    global _client
    if _client is None:
        _client = OpenSearch(
            hosts=[{"host": settings.opensearch_host, "port": settings.opensearch_port}],
            http_auth=(settings.opensearch_username, settings.opensearch_password),
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False,
        )
        logger.info(f"Connected to OpenSearch at {settings.opensearch_url}")
    return _client


def create_papers_index():
    """Create papers BM25 index with proper mappings."""
    client = get_client()

    index_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "default": {
                        "type": "standard"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "external_id": {"type": "keyword"},
                "title": {"type": "text", "boost": 2.0},
                "abstract": {"type": "text"},
                "authors": {"type": "text"},
                "venue": {"type": "keyword"},
                "concepts": {"type": "text", "boost": 1.2},
                "year": {"type": "integer"},
                "doi": {"type": "keyword"},
            }
        }
    }

    try:
        client.indices.delete(index=PAPERS_INDEX)
        logger.info(f"Deleted existing index: {PAPERS_INDEX}")
    except NotFoundError:
        pass

    client.indices.create(index=PAPERS_INDEX, body=index_body)
    logger.info(f"Created index: {PAPERS_INDEX}")


def create_startups_index():
    """Create startups BM25 index with proper mappings."""
    client = get_client()

    index_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "external_id": {"type": "keyword"},
                "name": {"type": "text", "boost": 2.0},
                "title": {"type": "text", "boost": 2.0},
                "one_liner": {"type": "text"},
                "description": {"type": "text"},
                "industry": {"type": "text", "boost": 1.2},
                "stage": {"type": "keyword"},
                "country": {"type": "keyword"},
                "website": {"type": "keyword"},
                "year": {"type": "integer"},
            }
        }
    }

    try:
        client.indices.delete(index=STARTUPS_INDEX)
        logger.info(f"Deleted existing index: {STARTUPS_INDEX}")
    except NotFoundError:
        pass

    client.indices.create(index=STARTUPS_INDEX, body=index_body)
    logger.info(f"Created index: {STARTUPS_INDEX}")


def index_papers_bulk(papers: List[Dict[str, Any]]):
    """Bulk index papers into OpenSearch."""
    client = get_client()

    actions = [
        {
            "_index": PAPERS_INDEX,
            "_id": paper["doc_id"],
            "_source": paper,
        }
        for paper in papers
    ]

    success, failed = helpers.bulk(client, actions, raise_on_error=False)
    logger.info(f"Indexed {success} papers, {failed} failed")
    return success, failed


def index_startups_bulk(startups: List[Dict[str, Any]]):
    """Bulk index startups into OpenSearch."""
    client = get_client()

    actions = [
        {
            "_index": STARTUPS_INDEX,
            "_id": startup["doc_id"],
            "_source": startup,
        }
        for startup in startups
    ]

    success, failed = helpers.bulk(client, actions, raise_on_error=False)
    logger.info(f"Indexed {success} startups, {failed} failed")
    return success, failed


def search_papers(query: str, top_k: int = 200, year_gte: int | None = None) -> List[dict]:
    """
    Search papers using BM25.

    Args:
        query: Search query
        top_k: Number of results to return
        year_gte: Filter by minimum year

    Returns:
        List of search results with scores
    """
    client = get_client()

    must_clauses = [
        {
            "multi_match": {
                "query": query,
                "fields": ["title^2", "abstract", "concepts^1.2", "authors"],
                "type": "best_fields",
            }
        }
    ]

    if year_gte:
        must_clauses.append({"range": {"year": {"gte": year_gte}}})

    search_body = {
        "query": {"bool": {"must": must_clauses}},
        "size": top_k,
        "_source": ["doc_id", "title", "abstract", "year", "venue", "concepts", "authors", "doi"],
    }

    results = client.search(index=PAPERS_INDEX, body=search_body)

    return [
        {
            "doc_id": hit["_source"]["doc_id"],
            "score": hit["_score"],
            "title": hit["_source"]["title"],
            "snippet": hit["_source"].get("abstract", "")[:300],
            "metadata": {
                "year": hit["_source"].get("year"),
                "venue": hit["_source"].get("venue"),
                "concepts": hit["_source"].get("concepts", []),
                "authors": hit["_source"].get("authors", []),
                "doi": hit["_source"].get("doi"),
            },
        }
        for hit in results["hits"]["hits"]
    ]


def search_startups(query: str, top_k: int = 200, year_gte: int | None = None) -> List[dict]:
    """
    Search startups using BM25.

    Args:
        query: Search query
        top_k: Number of results to return
        year_gte: Filter by minimum year

    Returns:
        List of search results with scores
    """
    client = get_client()

    must_clauses = [
        {
            "multi_match": {
                "query": query,
                "fields": ["title^2", "name^2", "description", "one_liner", "industry^1.2"],
                "type": "best_fields",
            }
        }
    ]

    if year_gte:
        must_clauses.append({"range": {"year": {"gte": year_gte}}})

    search_body = {
        "query": {"bool": {"must": must_clauses}},
        "size": top_k,
        "_source": ["doc_id", "title", "name", "description", "one_liner", "year", "industry", "stage", "website"],
    }

    results = client.search(index=STARTUPS_INDEX, body=search_body)

    return [
        {
            "doc_id": hit["_source"]["doc_id"],
            "score": hit["_score"],
            "title": hit["_source"].get("title", hit["_source"].get("name", "")),
            "snippet": hit["_source"].get("description", hit["_source"].get("one_liner", ""))[:300],
            "metadata": {
                "year": hit["_source"].get("year"),
                "industry": hit["_source"].get("industry", []),
                "stage": hit["_source"].get("stage"),
                "website": hit["_source"].get("website"),
            },
        }
        for hit in results["hits"]["hits"]
    ]
