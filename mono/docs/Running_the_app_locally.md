# Running the R&D Discovery System Locally

This guide walks you through setting up and running the R&D Discovery System on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

- **Node.js** 20+ (LTS version)
  ```bash
  node --version  # Should be v20.x.x or higher
  ```

- **Python** 3.11+
  ```bash
  python --version  # Should be 3.11.x or higher
  ```

- **Yarn** 1.22+
  ```bash
  yarn --version  # Should be 1.22.x or higher
  ```

- **Docker** & **Docker Compose**
  ```bash
  docker --version
  docker-compose --version
  ```

### Required API Keys

You'll need API keys from these services:

1. **OpenAI** - For summarization (GPT-4o-mini)
   - Get key: https://platform.openai.com/api-keys

2. **Cohere** - For reranking
   - Get key: https://dashboard.cohere.com/api-keys

3. **Pinecone** - For vector storage
   - Get key: https://app.pinecone.io/

4. **Tavily** - For real-time web search (startups)
   - Get key: https://tavily.com/

---

## Setup Instructions

### Step 1: Clone and Install Dependencies

```bash
# Navigate to the mono directory
cd /Users/aashmanrastogi/Desktop/RnD/mono

# Install all dependencies
yarn install
```

This will install dependencies for:
- Root workspace
- TypeScript API (`backend/api`)
- Next.js frontend (`apps/next`)
- Shared packages (`packages/prisma`, `packages/universal`)

### Step 2: Configure Environment Variables

1. **Copy the sample environment file**:
   ```bash
   cp .env.sample .env
   ```

2. **Edit `.env` with your API keys**:
   ```bash
   # Open in your preferred editor
   nano .env
   # or
   code .env
   ```

3. **Fill in the required values**:
   ```bash
   # OpenAI (REQUIRED)
   OPENAI_API_KEY=sk-your-actual-openai-key-here

   # Cohere (REQUIRED)
   COHERE_API_KEY=your-actual-cohere-key-here

   # Pinecone (REQUIRED)
   PINECONE_API_KEY=your-actual-pinecone-key-here
   PINECONE_INDEX_NAME=r2d-chunks
   PINECONE_CLOUD=aws
   PINECONE_ENVIRONMENT=us-west-2

   # Tavily (REQUIRED)
   TAVILY_API_KEY=your-actual-tavily-key-here

   # Admin token for protected endpoints
   ADMIN_BEARER_TOKEN=your-secure-token-here

   # Database (default values for local development)
   DATABASE_URL=postgresql://r2d:r2d@localhost:5432/r2d
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=r2d
   POSTGRES_USER=r2d
   POSTGRES_PASSWORD=r2d

   # OpenSearch (default values for local development)
   OPENSEARCH_HOST=localhost
   OPENSEARCH_PORT=9200
   OPENSEARCH_USERNAME=admin
   OPENSEARCH_PASSWORD=admin

   # Service URLs (for local development)
   LITELLM_SERVICE_URL=http://localhost:8001
   LLAMA_INDEXER_SERVICE_URL=http://localhost:8002
   TAVILY_SERVICE_URL=http://localhost:8003
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

### Step 3: Create Pinecone Index

**Important**: You must manually create the Pinecone index before running the system.

1. **Go to Pinecone console**: https://app.pinecone.io/

2. **Create a new Serverless index**:
   - Click "Create Index"
   - **Name**: `r2d-chunks`
   - **Dimensions**: `768` (for e5-base-v2 embeddings)
   - **Metric**: `cosine`
   - **Cloud**: `AWS`
   - **Region**: `us-west-2`

3. **Wait for index to be ready** (usually takes 1-2 minutes)

### Step 4: Start Infrastructure Services

Start PostgreSQL and OpenSearch using Docker:

```bash
docker-compose up -d postgres opensearch
```

**Verify services are running**:
```bash
# Check Docker containers
docker ps

# Should see:
# - mono-postgres-1   (port 5432)
# - mono-opensearch-1 (port 9200)

# Test PostgreSQL
docker exec -it mono-postgres-1 psql -U r2d -d r2d -c "SELECT 1;"

# Test OpenSearch
curl http://localhost:9200
```

### Step 5: Run Database Migrations

Apply Prisma database schema:

```bash
yarn workspace @r2d/prisma db:push
```

You should see output like:
```
✔ Generated Prisma Client
✔ The database is now in sync with the schema
```

### Step 6: Install Python Dependencies

Install Python packages for both services:

```bash
# LiteLLM service
cd backend/litellm
pip install -r requirements.txt
cd ../..

# Llama-Indexer service
cd backend/llama-indexer
pip install -r requirements.txt
cd ../..
```

**Tip**: Use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

---

## Running the Application

### Option 1: Run All Services with Turborepo (Recommended)

```bash
# From the mono/ directory
yarn dev
```

This starts all services simultaneously:
- TypeScript API: http://localhost:8000
- LiteLLM service: http://localhost:8001
- Llama-Indexer service: http://localhost:8002
- Next.js frontend: http://localhost:3000

### Option 2: Run Services Individually

Open 4 separate terminal windows:

**Terminal 1: TypeScript API**
```bash
yarn workspace @r2d/api dev
# Runs on http://localhost:8000
```

**Terminal 2: LiteLLM Service**
```bash
cd backend/litellm
python -m uvicorn server:app --reload --port 8001
# Runs on http://localhost:8001
```

**Terminal 3: Llama-Indexer Service**
```bash
cd backend/llama-indexer
python -m uvicorn app.main:app --reload --port 8002
# Runs on http://localhost:8002
```

**Terminal 4: Next.js Frontend**
```bash
yarn workspace @r2d/next dev
# Runs on http://localhost:3000
```

### Verify Services Are Running

```bash
# TypeScript API
curl http://localhost:8000/trpc/admin.health

# LiteLLM service
curl http://localhost:8001/health

# Llama-Indexer service
curl http://localhost:8002/health

# Frontend
curl http://localhost:3000
```

---

## Data Ingestion

Before you can search, you need to ingest data.

### Step 1: Create Search Indices

```bash
python scripts/build_indexes.py
```

This creates:
- OpenSearch indices: `papers_bm25`, `startups_bm25`
- Pinecone index (if not already created)

### Step 2: Ingest Papers

**Ingest from OpenAlex** (materials science, battery, biotech, ML):
```bash
python scripts/ingest_openalex.py
```

**Ingest from arXiv** (cs.LG, cond-mat.mtrl-sci):
```bash
python scripts/ingest_arxiv.py
```

**Expected output**:
```
✓ Fetched 200 works from OpenAlex
✓ Processed 185 papers (15 duplicates removed)
✓ Created 542 chunks
✓ Indexed in OpenSearch: 185 documents
✓ Upserted to Pinecone: 542 vectors
```

### Step 3: Ingest Startups

```bash
python scripts/ingest_startups.py
```

**Expected output**:
```
✓ Queried Perplexity with 20 seed queries
✓ Discovered 127 startups
✓ Processed 98 startups (29 duplicates removed)
✓ Created 245 chunks
✓ Indexed in OpenSearch: 98 documents
✓ Upserted to Pinecone: 245 vectors
```

### Or Run All Ingestion at Once

```bash
make ingest
```

---

## Using the Application

### Via Web UI (Recommended)

1. Open http://localhost:3000 in your browser

2. Enter a search query, e.g.:
   - "solid electrolyte batteries sub-zero temperature"
   - "CRISPR gene editing techniques"
   - "transformer attention mechanisms"

3. Apply filters:
   - Source: Papers, Startups, or Both
   - Year: Minimum publication year

4. Click "Summarize" on any result to generate structured summary

### Via API (tRPC)

**Search example**:
```bash
curl -X POST http://localhost:8000/trpc/search.search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "solid-state battery electrolytes",
    "filters": {
      "source": ["papers"],
      "year_gte": 2022
    },
    "limit": 10
  }'
```

**Summarize example**:
```bash
curl -X POST http://localhost:8000/trpc/search.summarize \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ["doc_id_1", "doc_id_2"]
  }'
```

**Trigger ingestion (admin only)**:
```bash
curl -X POST http://localhost:8000/trpc/ingest.openalex \
  -H "Authorization: Bearer your-admin-token"
```

---

## Troubleshooting

### Common Issues

#### 1. "Pinecone API key missing" Error

**Symptom**: API won't start
**Solution**:
```bash
# Check .env file has the key
cat .env | grep PINECONE_API_KEY

# Make sure it's not a placeholder
# Should be: PINECONE_API_KEY=your-actual-key-here
# NOT: PINECONE_API_KEY=your-pinecone-key-here
```

#### 2. "Index not found" Error

**Symptom**: Search returns 500 error
**Solution**:
```bash
# Check if Pinecone index exists
curl http://localhost:8002/health

# If pinecone_stats is null, create the index manually in Pinecone console
```

#### 3. OpenSearch Connection Refused

**Symptom**: `ConnectionRefusedError: [Errno 61] Connection refused`
**Solution**:
```bash
# Check if OpenSearch is running
docker ps | grep opensearch

# If not running, start it
docker-compose up -d opensearch

# Check logs
docker logs mono-opensearch-1
```

#### 4. "Database does not exist" Error

**Symptom**: `database "r2d" does not exist`
**Solution**:
```bash
# Recreate database
docker exec -it mono-postgres-1 psql -U r2d -c "CREATE DATABASE r2d;"

# Run migrations again
yarn workspace @r2d/prisma db:push
```

#### 5. Port Already in Use

**Symptom**: `Error: listen EADDRINUSE: address already in use :::8000`
**Solution**:
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port (update .env)
```

#### 6. Search Returns No Results

**Symptom**: Empty results array
**Solution**:
```bash
# Check if data was ingested
curl http://localhost:9200/papers_bm25/_count
curl http://localhost:9200/startups_bm25/_count

# Should return: {"count": 185} or similar

# If count is 0, run ingestion again
python scripts/ingest_openalex.py
```

#### 7. Python Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'fastapi'`
**Solution**:
```bash
# Make sure you installed dependencies
cd backend/litellm && pip install -r requirements.txt
cd backend/llama-indexer && pip install -r requirements.txt

# Or use the correct Python environment
source venv/bin/activate
```

---

## Testing

### Run All Tests

```bash
make test
```

### Run Specific Tests

**Backend API (TypeScript)**:
```bash
yarn workspace @r2d/api test
```

**Frontend**:
```bash
yarn workspace @r2d/next test
```

**Python Services**:
```bash
cd backend/llama-indexer
pytest

cd backend/litellm
pytest
```

---

## Evaluation

Evaluate search quality with nDCG@10 metric:

```bash
make eval
# or
python scripts/eval_ndcg.py
```

**Expected output**:
```
📊 Evaluating search quality...

Method             | nDCG@10
-------------------|--------
BM25 only         | 0.722
ANN only          | 0.754
Hybrid            | 0.819
Hybrid + Rerank   | 0.891 ✅

✅ All quality checks passed!
```

---

## Stopping the Application

### Stop All Services

```bash
# Stop Docker containers
docker-compose down

# Stop Turborepo dev servers
# Press Ctrl+C in the terminal running `yarn dev`
```

### Clean Everything (Including Data)

```bash
# Stop and remove all containers + volumes
docker-compose down -v

# Clean build artifacts
yarn clean
```

---

## Next Steps

- Read [ARCHITECTURE.md](../ARCHITECTURE.md) for system design
- See [README.md](../README.md) for API documentation
- Check [IMPLEMENTATION_PROMPT.md](../IMPLEMENTATION_PROMPT.md) for extending the system

---

**Need Help?** Create an issue in the repository or check the troubleshooting section above.

**Last Updated**: January 2025
