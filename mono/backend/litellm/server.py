"""
LiteLLM Service - FastAPI server for document summarization.

Handles:
- Summarization with OpenAI GPT-4o-mini
"""
import logging
import sys
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import custom implementations
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
    title="LiteLLM Service",
    description="Document summarization service using OpenAI GPT-4o-mini",
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
    return {"status": "ok", "service": "LiteLLM"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "LiteLLM"}


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
