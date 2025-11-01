"""Text chunking service for semantic splitting."""
import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Target chunk size in tokens (approximate)
TARGET_CHUNK_TOKENS = 512
STRIDE_TOKENS = 64

# Rough approximation: 1 token ≈ 4 characters for English text
CHARS_PER_TOKEN = 4
TARGET_CHUNK_CHARS = TARGET_CHUNK_TOKENS * CHARS_PER_TOKEN
STRIDE_CHARS = STRIDE_TOKENS * CHARS_PER_TOKEN


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using simple heuristics.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Simple sentence splitting (could be enhanced with NLTK or spaCy)
    # Split on periods, exclamation marks, question marks followed by space/newline
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(
    text: str,
    doc_id: str,
    source: str,
    title: str,
    section: str = "content",
) -> List[dict]:
    """
    Chunk text into semantic chunks with overlapping stride.

    Args:
        text: Text to chunk
        doc_id: Document ID
        source: Source type (papers/startups)
        title: Document title
        section: Section name (abstract, introduction, etc.)

    Returns:
        List of chunk dictionaries with metadata
    """
    if not text or not text.strip():
        return []

    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_length = 0
    chunk_index = 0

    for sentence in sentences:
        sentence_length = len(sentence)

        # If adding this sentence exceeds target, finalize current chunk
        if current_length + sentence_length > TARGET_CHUNK_CHARS and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "doc_id": doc_id,
                "chunk_index": chunk_index,
                "text": chunk_text,
                "section": section,
                "source": source,
                "title": title,
            })
            chunk_index += 1

            # Keep last portion for stride (overlap)
            # Remove sentences until we're under stride length
            while current_chunk and current_length > STRIDE_CHARS:
                removed = current_chunk.pop(0)
                current_length -= len(removed) + 1  # +1 for space

            current_chunk.append(sentence)
            current_length = sum(len(s) for s in current_chunk) + len(current_chunk) - 1
        else:
            current_chunk.append(sentence)
            current_length += sentence_length + (1 if current_chunk else 0)

    # Add remaining text as final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append({
            "doc_id": doc_id,
            "chunk_index": chunk_index,
            "text": chunk_text,
            "section": section,
            "source": source,
            "title": title,
        })

    logger.debug(f"Chunked document {doc_id} into {len(chunks)} chunks")
    return chunks


def chunk_document(
    doc_id: str,
    source: str,
    title: str,
    abstract: str | None = None,
    description: str | None = None,
) -> List[dict]:
    """
    Chunk a full document (paper or startup).

    Args:
        doc_id: Document ID
        source: Source type
        title: Document title
        abstract: Paper abstract (for papers)
        description: Startup description (for startups)

    Returns:
        List of chunk dictionaries
    """
    all_chunks = []

    # Chunk abstract or description
    if abstract:
        chunks = chunk_text(abstract, doc_id, source, title, section="abstract")
        all_chunks.extend(chunks)
    elif description:
        chunks = chunk_text(description, doc_id, source, title, section="description")
        all_chunks.extend(chunks)

    return all_chunks
