"""Startup ingestion service using Perplexity API."""
import asyncio
import hashlib
import logging
import re
from datetime import datetime
from typing import Dict, List
from urllib.parse import urlparse

import asyncpg
import httpx
import yaml

from app.config import settings
from app.services import chunking, embeddings, opensearch_client, pinecone_client

logger = logging.getLogger(__name__)

# Perplexity API configuration
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "llama-3.1-sonar-small-128k-online"

# Default seed queries (can be loaded from YAML)
DEFAULT_SEED_QUERIES = {
    "materials": [
        "innovative materials science startups developing new composites",
        "advanced materials startups for aerospace and automotive",
        "sustainable materials companies working on biodegradable alternatives",
        "nanomaterials startups for industrial applications",
        "graphene and 2D materials startups",
    ],
    "battery": [
        "battery technology startups developing solid-state batteries",
        "lithium-ion alternatives and next-gen battery startups",
        "battery recycling and circular economy startups",
        "EV battery management system companies",
        "grid-scale energy storage startups",
    ],
    "biotech": [
        "synthetic biology startups engineering organisms",
        "gene therapy and CRISPR therapeutics companies",
        "personalized medicine and biotech diagnostics startups",
        "protein engineering and biologics startups",
        "microbiome therapeutics companies",
    ],
    "ai_ml": [
        "generative AI startups for enterprise applications",
        "computer vision and autonomous systems companies",
        "natural language processing and LLM startups",
        "AI for drug discovery and healthcare",
        "MLOps and AI infrastructure platforms",
    ],
}


def load_startup_queries(yaml_path: str | None = None) -> Dict[str, List[str]]:
    """
    Load startup seed queries from YAML file.

    Args:
        yaml_path: Path to YAML file with queries (optional)

    Returns:
        Dictionary mapping topics to query lists
    """
    if yaml_path:
        try:
            with open(yaml_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load queries from {yaml_path}: {e}")
    
    # Return default queries if no file provided or loading failed
    return DEFAULT_SEED_QUERIES


async def query_perplexity(query: str) -> str:
    """
    Query Perplexity API for startup information.

    Args:
        query: Search query about startups

    Returns:
        Response text from Perplexity
    """
    system_prompt = """You are a startup research assistant. When asked about startups in a specific domain, 
provide a concise list of real, recently founded companies (last 5 years preferred). For each startup, include:
- Company name
- Website URL
- One-sentence description
- Industry/sector
- Stage (seed, series A, B, etc.)

Format your response as a structured list that's easy to parse."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                PERPLEXITY_API_URL,
                json={
                    "model": PERPLEXITY_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2000,
                },
                headers={
                    "Authorization": f"Bearer {settings.perplexity_api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            return content

        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            raise


def extract_domain_from_url(url: str) -> str:
    """Extract domain from URL for deduplication."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove 'www.' prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url.lower()


def parse_startup_from_text(text: str) -> List[dict]:
    """
    Parse startup information from Perplexity response text.

    Args:
        text: Response text from Perplexity

    Returns:
        List of parsed startup dictionaries
    """
    startups = []
    
    # Split by lines and look for patterns
    lines = text.split("\n")
    
    current_startup = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for company name (often starts with number or bullet)
        # Pattern: "1. Company Name" or "- Company Name" or "**Company Name**"
        if re.match(r"^[\d\-\*]+[\.\):\s]", line) or line.startswith("**"):
            # Save previous startup if exists
            if current_startup and current_startup.get("name"):
                startups.append(current_startup)
            
            # Extract company name
            name = re.sub(r"^[\d\-\*]+[\.\):\s]+", "", line)
            name = name.replace("**", "").strip()
            
            # Extract URL if in same line
            url_match = re.search(r"https?://[^\s\)]+", name)
            if url_match:
                url = url_match.group(0)
                name = name.replace(url, "").strip()
                current_startup = {"name": name, "website": url}
            else:
                current_startup = {"name": name}
        
        # Look for website
        elif "website" in line.lower() or "url" in line.lower():
            url_match = re.search(r"https?://[^\s\)]+", line)
            if url_match:
                current_startup["website"] = url_match.group(0)
        
        # Look for description
        elif "description" in line.lower() or ":" in line:
            # Clean up and extract description
            desc = re.sub(r"^[^:]*:\s*", "", line)
            current_startup.setdefault("description", desc)
        
        # Look for industry
        elif "industry" in line.lower() or "sector" in line.lower():
            industry = re.sub(r"^[^:]*:\s*", "", line)
            current_startup["industry"] = industry
        
        # Look for stage
        elif "stage" in line.lower() or "series" in line.lower():
            stage = re.sub(r"^[^:]*:\s*", "", line)
            current_startup["stage"] = stage
        
        # If line contains URL, extract it
        elif "http" in line:
            url_match = re.search(r"https?://[^\s\)]+", line)
            if url_match and "website" not in current_startup:
                current_startup["website"] = url_match.group(0)
    
    # Add last startup
    if current_startup and current_startup.get("name"):
        startups.append(current_startup)
    
    return startups


def normalize_startup(startup: dict) -> dict | None:
    """
    Normalize startup data into our schema.

    Args:
        startup: Raw startup dictionary

    Returns:
        Normalized document dictionary or None if invalid
    """
    try:
        name = startup.get("name", "").strip()
        if not name:
            return None
        
        # Generate external ID from website or name
        website = startup.get("website", "").strip()
        if website:
            domain = extract_domain_from_url(website)
            external_id = hashlib.md5(domain.encode()).hexdigest()
        else:
            external_id = hashlib.md5(name.encode()).hexdigest()
        
        # Build description
        description = startup.get("description", name)
        if not description:
            description = name
        
        # Extract industry (can be list or string)
        industry = startup.get("industry", "")
        if isinstance(industry, str):
            industry = [industry] if industry else []
        
        # Extract stage
        stage = startup.get("stage", "")
        
        return {
            "external_id": external_id,
            "source": "STARTUP",
            "title": name,
            "description": description,
            "year": datetime.now().year,  # Use current year as discovery year
            "language": "en",
            "website": website or None,
            "oneLiner": description[:200],  # Use first part of description
            "stage": stage or None,
            "industry": industry,
            "country": None,  # Could be extracted from response if available
        }
    
    except Exception as e:
        logger.error(f"Error normalizing startup: {e}")
        return None


async def ingest_startups_via_perplexity(
    yaml_path: str | None = None
) -> dict:
    """
    Ingest startups via Perplexity API.

    Loads queries from YAML file, queries Perplexity for each,
    parses results, and indexes startups.

    Args:
        yaml_path: Path to YAML file with seed queries (optional)

    Returns:
        Statistics dictionary with counts
    """
    logger.info("Starting startup ingestion via Perplexity")
    start_time = datetime.now()

    # Initialize statistics
    stats = {
        "total_fetched": 0,
        "total_processed": 0,
        "total_indexed": 0,
        "error_count": 0,
        "errors": [],
    }

    # Load queries
    queries_by_topic = load_startup_queries(yaml_path)
    all_queries = []
    for topic, queries in queries_by_topic.items():
        all_queries.extend(queries)
    
    logger.info(f"Loaded {len(all_queries)} queries across {len(queries_by_topic)} topics")

    # Connect to database
    conn = await asyncpg.connect(settings.database_url)

    # Track seen domains for deduplication
    seen_domains = set()

    try:
        # Create ingestion run record
        run_id = await conn.fetchval(
            """
            INSERT INTO "IngestionRun" (source, status, "startedAt")
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            "STARTUP",
            "IN_PROGRESS",
            start_time,
        )
        logger.info(f"Created ingestion run: {run_id}")

        # Query Perplexity for each seed query
        for idx, query in enumerate(all_queries):
            logger.info(f"[{idx + 1}/{len(all_queries)}] Querying: {query}")
            
            try:
                # Query Perplexity
                response_text = await query_perplexity(query)
                
                # Parse startups from response
                startups = parse_startup_from_text(response_text)
                stats["total_fetched"] += len(startups)
                
                logger.info(f"Extracted {len(startups)} startups from response")
                
                # Process each startup
                for startup in startups:
                    try:
                        # Normalize startup data
                        normalized = normalize_startup(startup)
                        if not normalized:
                            stats["error_count"] += 1
                            continue
                        
                        # Deduplicate by domain
                        if normalized["website"]:
                            domain = extract_domain_from_url(normalized["website"])
                            if domain in seen_domains:
                                logger.debug(f"Skipping duplicate domain: {domain}")
                                continue
                            seen_domains.add(domain)
                        
                        # Check if document already exists
                        existing = await conn.fetchval(
                            'SELECT id FROM "Document" WHERE "externalId" = $1',
                            normalized["external_id"],
                        )

                        if existing:
                            logger.debug(f"Skipping existing startup: {normalized['title']}")
                            continue

                        # Insert document into database
                        doc_id = await conn.fetchval(
                            """
                            INSERT INTO "Document" (
                                source, "externalId", title, description, year, language,
                                website, "oneLiner", stage, industry, country
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            RETURNING id
                            """,
                            normalized["source"],
                            normalized["external_id"],
                            normalized["title"],
                            normalized["description"],
                            normalized["year"],
                            normalized["language"],
                            normalized["website"],
                            normalized["oneLiner"],
                            normalized["stage"],
                            normalized["industry"],
                            normalized["country"],
                        )

                        # Chunk the document (description)
                        chunks = chunking.chunk_document(
                            text=normalized["description"],
                            max_chunk_size=512,
                        )

                        # Generate embeddings and index chunks
                        for chunk_idx, chunk_text in enumerate(chunks):
                            # Insert chunk into database
                            chunk_id = await conn.fetchval(
                                """
                                INSERT INTO "Chunk" ("documentId", "chunkIndex", text, section)
                                VALUES ($1, $2, $3, $4)
                                RETURNING id
                                """,
                                doc_id,
                                chunk_idx,
                                chunk_text,
                                "description",
                            )

                            # Generate embedding
                            embedding = embeddings.embed_passage(chunk_text)

                            # Prepare metadata for Pinecone
                            metadata = {
                                "doc_id": doc_id,
                                "chunk_id": chunk_id,
                                "source": "startups",
                                "title": normalized["title"],
                                "year": normalized["year"],
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
                            "source": "startups",
                            "title": normalized["title"],
                            "snippet": normalized["description"][:1000],
                            "metadata": {
                                "year": normalized["year"],
                                "website": normalized["website"],
                                "industry": normalized["industry"],
                                "stage": normalized["stage"],
                            },
                        }
                        opensearch_client.index_startup(doc_id, opensearch_doc)

                        stats["total_processed"] += 1
                        stats["total_indexed"] += 1

                    except Exception as e:
                        error_msg = f"Error processing startup '{startup.get('name', 'unknown')}': {str(e)}"
                        logger.error(error_msg)
                        stats["error_count"] += 1
                        stats["errors"].append(error_msg[:500])
                
                # Rate limiting between queries
                await asyncio.sleep(2.0)
            
            except Exception as e:
                error_msg = f"Error querying '{query}': {str(e)}"
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
        f"Startup ingestion completed in {duration:.2f}s: "
        f"{stats['total_processed']}/{stats['total_fetched']} startups processed, "
        f"{stats['error_count']} errors"
    )

    return stats

