"""
LiteLLM Proxy Service - FastAPI server for LLM operations.

Handles:
- Reranking with Cohere Rerank v3
- Summarization with OpenAI GPT-4o-mini
"""
import logging
import sys
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import custom implementations
from custom.reranker import rerank_documents
from custom.summarizer import summarize_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LiteLLM Proxy Service",
    description="LLM operations service for reranking and summarization",
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
class RerankRequest(BaseModel):
    """Rerank request schema."""
    query: str = Field(..., min_length=1)
    documents: List[dict] = Field(..., min_items=1)
    top_n: int = Field(30, ge=1, le=100)


class RerankResponse(BaseModel):
    """Rerank response schema."""
    results: List[tuple]


class SummarizeRequest(BaseModel):
    """Summarize request schema."""
    documents: List[dict] = Field(..., min_items=1, max_items=10)


class SummarizeResponse(BaseModel):
    """Summarize response schema."""
    summaries: Dict[str, dict]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str


# Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint."""
    return {"status": "ok", "service": "LiteLLM Proxy"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "LiteLLM Proxy"}


@app.post("/rerank", response_model=RerankResponse)
async def rerank(request: RerankRequest):
    """
    Rerank documents using Cohere Rerank v3 API.

    Args:
        request: Rerank request with query, documents, and top_n

    Returns:
        Reranked documents with scores
    """
    try:
        logger.info(f"Reranking {len(request.documents)} documents")

        reranked = await rerank_documents(
            query=request.query,
            documents=request.documents,
            top_n=request.top_n,
        )

        logger.info(f"Reranked to top {len(reranked)} results")

        return {"results": reranked}

    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """
    Generate structured summaries using OpenAI GPT-4o-mini.

    Args:
        request: List of documents to summarize

    Returns:
        Dictionary mapping document IDs to summaries
    """
    try:
        logger.info(f"Summarizing {len(request.documents)} documents")

        summaries = await summarize_batch(request.documents)

        logger.info(f"Generated {len(summaries)} summaries")

        if not summaries:
            raise HTTPException(
                status_code=503, detail="Summarization service unavailable"
            )

        return {"summaries": summaries}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
