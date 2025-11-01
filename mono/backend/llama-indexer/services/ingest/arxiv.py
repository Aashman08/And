"""arXiv API ingestion service for academic papers."""
import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List

import asyncpg
import httpx

from app.config import settings
from app.services import chunking, embeddings, opensearch_client, pinecone_client

logger = logging.getLogger(__name__)

# arXiv API configuration
ARXIV_API_URL = "http://export.arxiv.org/api/query"
CATEGORIES = ["cs.LG", "cond-mat.mtrl-sci"]  # Machine Learning, Materials Science
YEARS_BACK = 3
PAPERS_PER_CATEGORY = 200


async def fetch_arxiv_papers(
    category: str,
    date_from: str,
    max_results: int = 200,
) -> List[dict]:
    """
    Fetch papers from arXiv API for a given category.

    Args:
        category: arXiv category (e.g., 'cs.LG')
        date_from: ISO date string (YYYYMMDD)
        max_results: Maximum number of results to fetch

    Returns:
        List of paper dictionaries
    """
    all_papers = []
    start = 0
    batch_size = 100  # arXiv recommends max 100 per request

    # Build search query: category and date range
    search_query = f"cat:{category} AND submittedDate:[{date_from} TO *]"

    async with httpx.AsyncClient(timeout=30.0) as client:
        while len(all_papers) < max_results:
            # Construct query parameters
            params = {
                "search_query": search_query,
                "start": start,
                "max_results": min(batch_size, max_results - len(all_papers)),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }

            try:
                response = await client.get(ARXIV_API_URL, params=params)
                response.raise_for_status()

                # Parse XML response
                root = ET.fromstring(response.content)
                
                # arXiv API uses Atom namespace
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)

                if not entries:
                    break  # No more results

                # Parse entries
                for entry in entries:
                    paper = {
                        "id": entry.find("atom:id", ns).text if entry.find("atom:id", ns) is not None else None,
                        "title": entry.find("atom:title", ns).text if entry.find("atom:title", ns) is not None else None,
                        "summary": entry.find("atom:summary", ns).text if entry.find("atom:summary", ns) is not None else None,
                        "published": entry.find("atom:published", ns).text if entry.find("atom:published", ns) is not None else None,
                        "authors": [
                            author.find("atom:name", ns).text
                            for author in entry.findall("atom:author", ns)
                            if author.find("atom:name", ns) is not None
                        ],
                        "categories": [
                            cat.get("term")
                            for cat in entry.findall("atom:category", ns)
                            if cat.get("term")
                        ],
                        "doi": None,  # Extract DOI from links if available
                    }

                    # Extract DOI from links
                    for link in entry.findall("atom:link", ns):
                        if link.get("title") == "doi":
                            paper["doi"] = link.get("href", "").replace("http://dx.doi.org/", "")

                    all_papers.append(paper)

                logger.info(
                    f"Fetched batch starting at {start} for category '{category}': "
                    f"{len(entries)} papers"
                )

                start += len(entries)

                # Rate limiting: be polite to arXiv (3 seconds recommended)
                await asyncio.sleep(3.0)

            except Exception as e:
                logger.error(f"Error fetching arXiv papers at start={start}: {e}")
                break

    logger.info(f"Total fetched for category '{category}': {len(all_papers)} papers")
    return all_papers


def normalize_arxiv_paper(paper: dict) -> dict | None:
    """
    Normalize arXiv paper data into our schema.

    Args:
        paper: Raw paper data from arXiv API

    Returns:
        Normalized document dictionary or None if invalid
    """
    try:
        # Extract arXiv ID from URL
        arxiv_id = paper.get("id", "")
        if "arxiv.org/abs/" in arxiv_id:
            arxiv_id = arxiv_id.split("arxiv.org/abs/")[-1]
        else:
            return None

        # Extract title and abstract
        title = paper.get("title", "").strip()
        # Clean up whitespace in title
        title = " ".join(title.split())
        
        abstract = paper.get("summary", "").strip()
        # Clean up whitespace in abstract
        abstract = " ".join(abstract.split())

        if not title or not abstract:
            return None

        # Extract year from published date
        published = paper.get("published", "")
        year = None
        if published:
            try:
                year = int(published[:4])
            except (ValueError, TypeError):
                pass

        # Extract authors (limit to 10)
        authors = paper.get("authors", [])[:10]

        # Extract DOI if available
        doi = paper.get("doi")

        # Extract categories (concepts)
        concepts = paper.get("categories", [])[:5]

        return {
            "external_id": arxiv_id,
            "source": "PAPER",
            "title": title,
            "description": abstract,
            "year": year,
            "language": "en",
            "doi": doi,
            "authors": authors,
            "venue": "arXiv",  # All papers are from arXiv
            "concepts": concepts,
        }

    except Exception as e:
        logger.error(f"Error normalizing arXiv paper: {e}")
        return None


async def ingest_arxiv_papers() -> dict:
    """
    Ingest papers from arXiv API.

    Fetches papers for predefined categories, stores in database,
    chunks content, generates embeddings, and indexes in search engines.

    Returns:
        Statistics dictionary with counts
    """
    logger.info("Starting arXiv ingestion")
    start_time = datetime.now()

    # Initialize statistics
    stats = {
        "total_fetched": 0,
        "total_processed": 0,
        "total_indexed": 0,
        "error_count": 0,
        "errors": [],
    }

    # Calculate date threshold (YYYYMMDD format)
    date_threshold = datetime.now() - timedelta(days=YEARS_BACK * 365)
    date_from = date_threshold.strftime("%Y%m%d")

    # Connect to database
    conn = await asyncpg.connect(settings.database_url)

    try:
        # Create ingestion run record
        run_id = await conn.fetchval(
            """
            INSERT INTO "IngestionRun" (source, status, "startedAt")
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            "PAPER",
            "IN_PROGRESS",
            start_time,
        )
        logger.info(f"Created ingestion run: {run_id}")

        # Fetch papers for each category
        all_papers = []
        for category in CATEGORIES:
            logger.info(f"Fetching papers for category: {category}")
            papers = await fetch_arxiv_papers(category, date_from, PAPERS_PER_CATEGORY)
            all_papers.extend(papers)
            stats["total_fetched"] += len(papers)

        logger.info(f"Total fetched: {stats['total_fetched']} papers")

        # Process each paper
        for paper in all_papers:
            try:
                # Normalize paper data
                normalized = normalize_arxiv_paper(paper)
                if not normalized:
                    stats["error_count"] += 1
                    continue

                # Check if document already exists
                existing = await conn.fetchval(
                    'SELECT id FROM "Document" WHERE "externalId" = $1',
                    normalized["external_id"],
                )

                if existing:
                    logger.debug(f"Skipping existing document: {normalized['external_id']}")
                    continue

                # Insert document into database
                doc_id = await conn.fetchval(
                    """
                    INSERT INTO "Document" (
                        source, "externalId", title, description, year, language,
                        doi, authors, venue, concepts
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                    """,
                    normalized["source"],
                    normalized["external_id"],
                    normalized["title"],
                    normalized["description"],
                    normalized["year"],
                    normalized["language"],
                    normalized["doi"],
                    normalized["authors"],
                    normalized["venue"],
                    normalized["concepts"],
                )

                # Chunk the document
                chunks = chunking.chunk_document(
                    text=normalized["description"],
                    max_chunk_size=512,
                )

                # Generate embeddings and index chunks
                for idx, chunk_text in enumerate(chunks):
                    # Insert chunk into database
                    chunk_id = await conn.fetchval(
                        """
                        INSERT INTO "Chunk" ("documentId", "chunkIndex", text, section)
                        VALUES ($1, $2, $3, $4)
                        RETURNING id
                        """,
                        doc_id,
                        idx,
                        chunk_text,
                        "abstract",
                    )

                    # Generate embedding
                    embedding = embeddings.embed_passage(chunk_text)

                    # Prepare metadata for Pinecone
                    metadata = {
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "source": "papers",
                        "title": normalized["title"],
                        "year": normalized["year"] or 0,
                        "text": chunk_text[:1000],  # Store snippet
                    }

                    # Upsert to Pinecone
                    vector_id = f"chunk_{chunk_id}"
                    pinecone_client.upsert_vectors(
                        vectors=[(vector_id, embedding.tolist(), metadata)]
                    )

                    # Update chunk with vector ID
                    await conn.execute(
                        'UPDATE "Chunk" SET "vectorId" = $1 WHERE id = $2',
                        vector_id,
                        chunk_id,
                    )

                # Index document in OpenSearch
                opensearch_doc = {
                    "doc_id": doc_id,
                    "source": "papers",
                    "title": normalized["title"],
                    "snippet": normalized["description"][:1000],
                    "metadata": {
                        "year": normalized["year"],
                        "venue": normalized["venue"],
                        "concepts": normalized["concepts"],
                        "authors": normalized["authors"],
                        "doi": normalized["doi"],
                    },
                }
                opensearch_client.index_paper(doc_id, opensearch_doc)

                stats["total_processed"] += 1
                stats["total_indexed"] += 1

                if stats["total_processed"] % 10 == 0:
                    logger.info(f"Processed {stats['total_processed']} documents")

            except Exception as e:
                error_msg = f"Error processing paper: {str(e)}"
                logger.error(error_msg)
                stats["error_count"] += 1
                stats["errors"].append(error_msg[:500])

        # Update ingestion run
        await conn.execute(
            """
            UPDATE "IngestionRun"
            SET status = $1, "totalFetched" = $2, "totalProcessed" = $3,
                "totalIndexed" = $4, "errorCount" = $5, errors = $6, "completedAt" = $7
            WHERE id = $8
            """,
            "COMPLETED",
            stats["total_fetched"],
            stats["total_processed"],
            stats["total_indexed"],
            stats["error_count"],
            stats["errors"][:100],  # Limit error list
            datetime.now(),
            run_id,
        )

    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        stats["errors"].append(error_msg)
        raise

    finally:
        await conn.close()

    duration = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"arXiv ingestion completed in {duration:.2f}s: "
        f"{stats['total_processed']}/{stats['total_fetched']} documents processed, "
        f"{stats['error_count']} errors"
    )

    return stats

