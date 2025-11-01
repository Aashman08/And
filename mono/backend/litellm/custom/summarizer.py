"""Summarization service using LiteLLM with OpenAI gpt-4o-mini."""
import json
import logging
from typing import Dict

from litellm import completion

from app.config import settings

logger = logging.getLogger(__name__)


SUMMARIZATION_PROMPT = """You are an expert research analyst. Given the following document, extract a structured summary with exactly 5 sections:

1. **problem**: What problem or research question is being addressed?
2. **approach**: What methods, techniques, or approach is being used?
3. **evidence_or_signals**: What key evidence, data, signals, or traction is mentioned?
4. **result**: What are the main outcomes, findings, or achievements?
5. **limitations**: What limitations, challenges, or open questions remain?

Keep each section concise (1-2 sentences max). Be specific and factual.

Document Title: {title}
Source: {source}
Content: {content}

Return your response as a JSON object with keys: problem, approach, evidence_or_signals, result, limitations.
"""


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

        response = completion(
            model=settings.litellm_summarization_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
            api_key=settings.openai_api_key,
            timeout=settings.INTERNAL_OP_TIMEOUT / 1000,  # Convert to seconds
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
