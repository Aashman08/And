"""OpenAlex API ingestion service for academic papers."""
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List

import asyncpg
import httpx

from app.config import settings
from app.services import chunking, embeddings, opensearch_client, pinecone_client

logger = logging.getLogger(__name__)

# OpenAlex API configuration
OPENALEX_API_URL = "https://api.openalex.org/works"
OPENALEX_EMAIL = "research@example.com"  # Polite pool access
TOPICS = ["materials science", "battery", "biotechnology", "machine learning"]
YEARS_BACK = 3
WORKS_PER_TOPIC = 200


async def fetch_openalex_works(
    topic: str,
    year_gte: int,
    per_page: int = 200,
) -> List[dict]:
    """
    Fetch works from OpenAlex API for a given topic.

    Args:
        topic: Research topic to search for
        year_gte: Minimum publication year
        per_page: Results per page (max 200)

    Returns:
        List of work dictionaries
    """
    all_works = []
    page = 1

    # Build filter query
    filter_parts = [
        f"default.search:{topic}",
        f"publication_year:>={year_gte}",
        "language:en",
        "has_abstract:true",
    ]
    filter_query = ",".join(filter_parts)

    async with httpx.AsyncClient(timeout=30.0) as client:
        while len(all_works) < per_page:
            # Construct query with pagination
            params = {
                "filter": filter_query,
                "per_page": min(200, per_page - len(all_works)),
                "page": page,
                "mailto": OPENALEX_EMAIL,
                "select": "id,doi,title,abstract,publication_year,authorships,primary_location,concepts",
            }

            try:
                response = await client.get(OPENALEX_API_URL, params=params)
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                if not results:
                    break  # No more results

                all_works.extend(results)
                logger.info(f"Fetched page {page} for topic '{topic}': {len(results)} works")

                page += 1

                # Rate limiting: be polite to OpenAlex
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error fetching page {page} for topic '{topic}': {e}")
                break

    logger.info(f"Total fetched for topic '{topic}': {len(all_works)} works")
    return all_works


def normalize_openalex_work(work: dict) -> dict | None:
    """
    Normalize OpenAlex work data into our schema.

    Args:
        work: Raw work data from OpenAlex API

    Returns:
        Normalized document dictionary or None if invalid
    """
    try:
        # Extract DOI or use OpenAlex ID
        doi = work.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        external_id = doi or work.get("id", "").replace("https://openalex.org/", "")

        if not external_id:
            return None

        # Extract title and abstract
        title = work.get("title", "").strip()
        abstract = work.get("abstract", "")
        if isinstance(abstract, str):
            abstract = abstract.strip()
        else:
            abstract = ""

        if not title or not abstract:
            return None

        # Extract year
        year = work.get("publication_year")
        if not year or year < 1900:
            year = None

        # Extract authors
        authors = []
        for authorship in work.get("authorships", [])[:10]:  # Limit to 10 authors
            author = authorship.get("author", {})
            display_name = author.get("display_name")
            if display_name:
                authors.append(display_name)

        # Extract venue
        venue = None
        primary_location = work.get("primary_location", {})
        if primary_location:
            source = primary_location.get("source", {})
            venue = source.get("display_name")

        # Extract concepts (topics)
        concepts = []
        for concept in work.get("concepts", [])[:5]:  # Top 5 concepts
            display_name = concept.get("display_name")
            if display_name:
                concepts.append(display_name)

        return {
            "external_id": external_id,
            "source": "PAPER",
            "title": title,
            "description": abstract,
            "year": year,
            "language": "en",
            "doi": doi,
            "authors": authors,
            "venue": venue,
            "concepts": concepts,
        }

    except Exception as e:
        logger.error(f"Error normalizing work: {e}")
        return None


async def ingest_openalex_papers() -> dict:
    """
    Ingest papers from OpenAlex API.

    Fetches papers for predefined topics, stores in database,
    chunks content, generates embeddings, and indexes in search engines.

    Returns:
        Statistics dictionary with counts
    """
    logger.info("Starting OpenAlex ingestion")
    start_time = datetime.now()

    # Initialize statistics
    stats = {
        "total_fetched": 0,
        "total_processed": 0,
        "total_indexed": 0,
        "error_count": 0,
        "errors": [],
    }

    # Calculate year threshold
    current_year = datetime.now().year
    year_gte = current_year - YEARS_BACK

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

        # Fetch works for each topic
        all_works = []
        for topic in TOPICS:
            logger.info(f"Fetching works for topic: {topic}")
            works = await fetch_openalex_works(topic, year_gte, WORKS_PER_TOPIC)
            all_works.extend(works)
            stats["total_fetched"] += len(works)

        logger.info(f"Total fetched: {stats['total_fetched']} works")

        # Process each work
        for work in all_works:
            try:
                # Normalize work data
                normalized = normalize_openalex_work(work)
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
                error_msg = f"Error processing work: {str(e)}"
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
        f"OpenAlex ingestion completed in {duration:.2f}s: "
        f"{stats['total_processed']}/{stats['total_fetched']} documents processed, "
        f"{stats['error_count']} errors"
    )

    return stats

