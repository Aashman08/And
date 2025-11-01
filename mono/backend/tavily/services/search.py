"""Tavily web search implementation."""
import logging
from typing import List, Optional, Dict

import httpx

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

logger = logging.getLogger(__name__)

TAVILY_API_URL = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"


async def search_web(
    query: str,
    max_results: int = 10,
    search_depth: str = "basic",
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Perform web search using Tavily API.

    Args:
        query: Search query
        max_results: Maximum number of results to return
        search_depth: Search depth ("basic" or "advanced")
        include_domains: List of domains to include
        exclude_domains: List of domains to exclude

    Returns:
        List of search results with title, url, content, score
    """
    if not settings.tavily_api_key:
        logger.warning("Tavily API key not set, returning empty results")
        return []

    try:
        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }

        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TAVILY_API_URL, json=payload)
            response.raise_for_status()
            result = response.json()

        # Parse and return results
        results = result.get("results", [])
        
        # Normalize result format
        normalized = []
        for item in results:
            normalized.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "snippet": item.get("content", "")[:200],  # Short snippet
                "score": item.get("score", 0.0),
                "published_date": item.get("published_date"),
            })

        logger.info(f"Tavily search returned {len(normalized)} results")
        return normalized

    except httpx.HTTPStatusError as e:
        logger.error(f"Tavily API error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        raise


async def extract_url_content(urls: List[str]) -> Dict[str, str]:
    """
    Extract content from URLs using Tavily extract API.

    Args:
        urls: List of URLs to extract content from

    Returns:
        Dictionary mapping URLs to extracted content
    """
    if not settings.tavily_api_key:
        logger.warning("Tavily API key not set, returning empty content")
        return {}

    try:
        payload = {
            "api_key": settings.tavily_api_key,
            "urls": urls,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TAVILY_EXTRACT_URL, json=payload)
            response.raise_for_status()
            result = response.json()

        # Parse results
        content = {}
        for item in result.get("results", []):
            url = item.get("url")
            text = item.get("raw_content", "")
            if url and text:
                content[url] = text

        logger.info(f"Extracted content from {len(content)} URLs")
        return content

    except httpx.HTTPStatusError as e:
        logger.error(f"Tavily extract API error: {e.response.status_code}")
        raise
    except Exception as e:
        logger.error(f"Content extraction failed: {e}")
        raise

