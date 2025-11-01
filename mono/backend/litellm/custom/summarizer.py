"""Summarization service using LiteLLM with OpenAI gpt-4o-mini."""
import json
import logging
from typing import Dict

from litellm import completion

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from prompts import SUMMARIZATION_PROMPT

logger = logging.getLogger(__name__)


async def summarize_document(
    doc_id: str,
    
    title: str,
    content: str,
    source: str,
) -> Dict[str, str]:
    """
    Generate structured summary for a single document.

    Args:
        doc_id: Document ID
        title: Document title
        content: Document content (abstract/description)
        source: Source type (papers/startups)

    Returns:
        Dictionary with 5 summary sections
    """
    try:
        prompt = SUMMARIZATION_PROMPT.format(
            title=title,
            source=source,
            content=content[:4000],  # Truncate if too long
        )

        # Set API key in environment for LiteLLM
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        
        response = completion(
            model=settings.litellm_summarization_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},  # Force JSON output

        )

        content = response.choices[0].message.content

        # Try to parse JSON response
        try:
            summary = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: extract sections manually
            logger.warning(f"Failed to parse JSON summary for {doc_id}, using fallback")
            summary = {
                "problem": "Unable to extract problem statement",
                "approach": "Unable to extract approach",
                "evidence_or_signals": "Unable to extract evidence",
                "result": "Unable to extract results",
                "limitations": "Unable to extract limitations",
            }

        # Ensure all required keys exist
        required_keys = ["problem", "approach", "evidence_or_signals", "result", "limitations"]
        for key in required_keys:
            if key not in summary:
                summary[key] = f"No {key} information available"

        return summary

    except Exception as e:
        logger.error(f"Summarization failed for {doc_id}: {e}")
        raise


async def summarize_batch(documents: list[dict]) -> Dict[str, Dict[str, str]]:
    """
    Summarize multiple documents.

    Args:
        documents: List of document dictionaries with id, title, content, source

    Returns:
        Dictionary mapping doc_id to summary
    """
    summaries = {}

    for doc in documents:
        try:
            summary = await summarize_document(
                doc_id=doc["id"],
                title=doc["title"],
                content=doc["content"],
                source=doc["source"],
            )
            summaries[doc["id"]] = summary
        except Exception as e:
            logger.error(f"Failed to summarize {doc['id']}: {e}")
            # Don't include failed summarizations

    return summaries
