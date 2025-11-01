"""
Tavily Service - FastAPI server for real-time web search.

Handles:
- Web search via Tavily API
- URL content extraction
- Fresh data retrieval
"""
import logging
import sys
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import services
from services.search import search_web, extract_url_content

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Tavily Service",
    description="Real-time web search service using Tavily API",
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
class WebSearchRequest(BaseModel):
    """Web search request schema."""
    query: str = Field(..., min_length=1, max_length=512)
    max_results: int = Field(10, ge=1, le=20)
    search_depth: str = Field("basic", pattern="^(basic|advanced)$")
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None


class WebSearchResponse(BaseModel):
    """Web search response schema."""
    results: List[dict]
    total: int


class ExtractContentRequest(BaseModel):
    """URL content extraction request."""
    urls: List[str] = Field(..., min_items=1, max_items=10)


class ExtractContentResponse(BaseModel):
    """URL content extraction response."""
    content: dict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str


# Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint."""
    return {"status": "ok", "service": "Tavily"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "Tavily"}


@app.post("/search", response_model=WebSearchResponse)
async def search(request: WebSearchRequest):
    """
    Perform real-time web search using Tavily API.

    Args:
        request: Search query and parameters

    Returns:
        List of web search results
    """
    try:
        logger.info(f"Web search for: {request.query}")

        results = await search_web(
            query=request.query,
            max_results=request.max_results,
            search_depth=request.search_depth,
            include_domains=request.include_domains,
            exclude_domains=request.exclude_domains,
        )

        logger.info(f"Found {len(results)} web results")

        return {
            "results": results,
            "total": len(results),
        }

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract", response_model=ExtractContentResponse)
async def extract(request: ExtractContentRequest):
    """
    Extract content from URLs.

    Args:
        request: List of URLs to extract content from

    Returns:
        Extracted content from URLs
    """
    try:
        logger.info(f"Extracting content from {len(request.urls)} URLs")

        content = await extract_url_content(urls=request.urls)

        logger.info(f"Extracted content from {len(content)} URLs")

        return {"content": content}

    except Exception as e:
        logger.error(f"Content extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")

