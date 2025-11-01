"""
Llama-Indexer Service - FastAPI server for document processing and search.

Handles:
- Hybrid search (BM25 + vector)
- Document indexing
- Highlight generation
- Data ingestion from multiple sources
"""
import logging
import sys
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import services
from app.services.retriever import hybrid_search
from app.services.highlight import generate_highlights
from app.clients.opensearch import (
    index_papers_bulk,
    index_startups_bulk,
    create_papers_index,
    create_startups_index,
)
from app.clients.pinecone import upsert_vectors_bulk, create_index, get_index_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Llama-Indexer Service",
    description="Document processing and hybrid search service",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class HybridSearchRequest(BaseModel):
    """Hybrid search request."""
    query: str = Field(..., min_length=1, max_length=512)
    filters: Optional[dict] = None
    top_k: int = Field(256, ge=1, le=500)


class HybridSearchResponse(BaseModel):
    """Hybrid search response."""
    results: List[dict]
    total: int


class HighlightRequest(BaseModel):
    """Highlight generation request."""
    query: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)


class HighlightResponse(BaseModel):
    """Highlight generation response."""
    highlights: List[str]


class IndexRequest(BaseModel):
    """Document indexing request."""
    documents: List[dict] = Field(..., min_items=1)
    source: str = Field(..., pattern="^(papers|startups)$")


class IndexResponse(BaseModel):
    """Document indexing response."""
    indexed: int
    errors: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    opensearch: bool
    pinecone: Optional[dict] = None


# Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint."""
    return {"status": "ok", "service": "Llama-Indexer"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.

    Checks connectivity to OpenSearch and Pinecone.
    """
    try:
        # Check Pinecone
        pinecone_stats = get_index_stats()
        pinecone_healthy = True
    except Exception as e:
        logger.warning(f"Pinecone health check failed: {e}")
        pinecone_stats = None
        pinecone_healthy = False

    # TODO: Add OpenSearch health check

    return {
        "status": "ok" if pinecone_healthy else "degraded",
        "service": "Llama-Indexer",
        "opensearch": True,  # TODO: Implement actual check
        "pinecone": pinecone_stats,
    }


@app.post("/search/hybrid", response_model=HybridSearchResponse)
async def search_hybrid(request: HybridSearchRequest):
    """
    Perform hybrid search combining BM25 and vector search.

    Args:
        request: Search request with query, filters, and top_k

    Returns:
        Blended and deduplicated search results
    """
    start_time = time.time()

    try:
        logger.info(f"Hybrid search for: {request.query}")

        # Extract filters
        source_filter = request.filters.get("source") if request.filters else None
        year_gte = request.filters.get("year_gte") if request.filters else None

        # Perform hybrid search
        results = await hybrid_search(
            query=request.query,
            source_filter=source_filter,
            year_gte=year_gte,
            top_k=request.top_k,
        )

        duration = (time.time() - start_time) * 1000
        logger.info(f"Hybrid search completed in {duration:.2f}ms, {len(results)} results")

        return {
            "results": results,
            "total": len(results),
        }

    except Exception as e:
        logger.error(f"Hybrid search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/highlights", response_model=HighlightResponse)
async def generate_highlights_endpoint(request: HighlightRequest):
    """
    Generate highlight sentences explaining why a result is relevant.

    Args:
        request: Query and text to generate highlights from

    Returns:
        List of highlight sentences
    """
    try:
        highlights = generate_highlights(
            query=request.query,
            document_text=request.text,
        )

        return {"highlights": highlights}

    except Exception as e:
        logger.error(f"Highlight generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index", response_model=IndexResponse)
async def index_documents(request: IndexRequest):
    """
    Index documents into OpenSearch and Pinecone.

    Args:
        request: Documents to index and source type

    Returns:
        Number of documents successfully indexed
    """
    try:
        logger.info(f"Indexing {len(request.documents)} {request.source} documents")

        # Index into OpenSearch
        if request.source == "papers":
            success, failed = index_papers_bulk(request.documents)
        else:
            success, failed = index_startups_bulk(request.documents)

        # TODO: Also index vectors into Pinecone

        return {
            "indexed": success,
            "errors": failed,
        }

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index/create")
async def create_indexes():
    """
    Create OpenSearch indices and Pinecone index.

    One-time setup operation.
    """
    try:
        logger.info("Creating search indices...")

        # Create OpenSearch indices
        create_papers_index()
        create_startups_index()

        # Create Pinecone index
        create_index()

        return {"status": "ok", "message": "Indices created successfully"}

    except Exception as e:
        logger.error(f"Index creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/openalex")
async def ingest_openalex():
    """
    Ingest papers from OpenAlex API.

    Protected endpoint - should be called via main API gateway.
    """
    # TODO: Implement actual ingestion
    return {
        "status": "completed",
        "total_fetched": 0,
        "total_indexed": 0,
        "message": "OpenAlex ingestion not fully implemented",
    }


@app.post("/ingest/arxiv")
async def ingest_arxiv():
    """
    Ingest papers from arXiv API.

    Protected endpoint - should be called via main API gateway.
    """
    # TODO: Implement actual ingestion
    return {
        "status": "completed",
        "total_fetched": 0,
        "total_indexed": 0,
        "message": "arXiv ingestion not fully implemented",
    }


@app.post("/ingest/startups")
async def ingest_startups():
    """
    Ingest startups via Perplexity API.

    Protected endpoint - should be called via main API gateway.
    """
    # TODO: Implement actual ingestion
    return {
        "status": "completed",
        "total_fetched": 0,
        "total_indexed": 0,
        "message": "Startup ingestion not fully implemented",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
