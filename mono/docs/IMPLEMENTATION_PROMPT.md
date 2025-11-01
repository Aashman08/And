# Complete R&D Discovery System - Implementation Prompt for LLM

## Context

You are completing an R&D discovery system monorepo. The architecture has been restructured from a single FastAPI backend to a **microservices architecture**:

- **TypeScript tRPC API** (backend/api/) - Orchestration layer
- **Python LiteLLM service** (backend/litellm/) - LLM operations
- **Python Llama-Indexer service** (backend/llama-indexer/) - Document processing & search
- **Next.js frontend** (apps/next/) - User interface

## What's Complete

✅ Repository structure with Turborepo + Yarn workspaces
✅ TypeScript tRPC API gateway with routers, procedures, and service clients
✅ Prisma schema (Document, Chunk, IngestionRun models)
✅ Shared packages (@r2d/prisma, @r2d/universal)
✅ Python service code (needs reorganization - see below)

## Your Task: Complete the Remaining Components

Work location: `/Users/aashmanrastogi/Desktop/RnD/mono/`

### PHASE 1: Reorganize Python Code into Microservices

**Current situation**: Python code is in `backend-temp/api/app/services/`

#### 1.1: Create `backend/litellm/` Service

**Purpose**: Handle all LLM API calls (OpenAI, Cohere)

**Files to create**:

```python
# backend/litellm/server.py
"""
FastAPI server for LiteLLM proxy service.
Endpoints:
- POST /rerank: Cohere reranking
- POST /summarize: OpenAI summarization
- GET /health: Health check
"""

# backend/litellm/custom/reranker.py
# Move content from: backend-temp/api/app/services/reranker.py
# Keep the Cohere Rerank v3 implementation

# backend/litellm/custom/summarizer.py
# Move content from: backend-temp/api/app/services/summarizer.py
# Keep the LiteLLM + OpenAI summarization

# backend/litellm/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
litellm==1.49.4
pydantic==2.9.2
pydantic-settings==2.5.2
httpx==0.27.2
python-dotenv==1.0.1

# backend/litellm/config.yaml
# LiteLLM configuration for model routing
model_list:
  - model_name: gpt-4o-mini
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY
  - model_name: command-r
    litellm_params:
      model: cohere/command-r
      api_key: os.environ/COHERE_API_KEY

# backend/litellm/package.json
{
  "name": "@r2d/litellm",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "uvicorn server:app --reload --port 8001",
    "start": "uvicorn server:app --host 0.0.0.0 --port 8001"
  }
}
```

**Implementation requirements**:
- FastAPI app with CORS enabled
- POST /rerank: Accept { query, documents, top_n }, return reranked list
- POST /summarize: Accept { documents: [{id, title, content, source}] }, return { summaries: {id: {problem, approach, ...}} }
- Use httpx to call Cohere Rerank API directly
- Use LiteLLM for OpenAI calls
- Proper error handling with fallbacks where appropriate
- Structured logging

#### 1.2: Create `backend/llama-indexer/` Service

**Purpose**: Document processing, embedding, and hybrid search

**Files to create**:

```python
# backend/llama-indexer/app/main.py
"""
FastAPI server for document indexing and retrieval.
Endpoints:
- POST /search/hybrid: Hybrid BM25 + vector search
- POST /highlights: Generate highlight sentences
- POST /index: Index documents
- POST /ingest/openalex: Ingest from OpenAlex
- POST /ingest/arxiv: Ingest from arXiv
- POST /ingest/startups: Ingest from Perplexity
- GET /health: Health check
"""

# Move these files from backend-temp/api/app/services/:
# - embeddings.py → backend/llama-indexer/app/services/embeddings.py
# - chunking.py → backend/llama-indexer/app/services/chunking.py
# - opensearch_client.py → backend/llama-indexer/app/clients/opensearch.py
# - pinecone_client.py → backend/llama-indexer/app/clients/pinecone.py
# - retriever.py → backend/llama-indexer/app/services/retriever.py
# - highlight.py → backend/llama-indexer/app/services/highlight.py

# Create new ingestion services:
# backend/llama-indexer/app/services/ingest/openalex.py
# backend/llama-indexer/app/services/ingest/arxiv.py
# backend/llama-indexer/app/services/ingest/startups.py

# backend/llama-indexer/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
pydantic-settings==2.5.2
sentence-transformers==2.7.0
torch==2.5.1
numpy==1.26.4
opensearch-py==2.7.1
pinecone-client==5.0.1
psycopg2-binary==2.9.9
asyncpg==0.29.0
httpx==0.27.2
aiohttp==3.10.10
pyyaml==6.0.2
python-dotenv==1.0.1

# backend/llama-indexer/package.json
{
  "name": "@r2d/llama-indexer",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "uvicorn app.main:app --reload --port 8002",
    "start": "uvicorn app.main:app --host 0.0.0.0 --port 8002"
  }
}

# backend/llama-indexer/app/config.py
# Pydantic settings for configuration
```

**Implementation requirements**:
- FastAPI app with all endpoints
- POST /search/hybrid: Call retriever.hybrid_search()
- POST /highlights: Call highlight.generate_highlights()
- POST /index: Bulk index documents to OpenSearch + Pinecone
- Ingestion endpoints: Fetch from APIs, process, chunk, embed, index
- Use existing Python service code (just reorganize)
- Database access via psycopg2 or asyncpg (not Prisma - that's Node.js only)
- Proper async/await patterns
- Error handling and logging

### PHASE 2: Complete Frontend (apps/next/)

**Current state**: Basic Next.js structure exists

**Create these files**:

```typescript
// apps/next/package.json
{
  "name": "@r2d/next",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@r2d/universal": "workspace:*",
    "@trpc/client": "^10.45.0",
    "@trpc/server": "^10.45.0",
    "@trpc/react-query": "^10.45.0",
    "@tanstack/react-query": "^5.17.9",
    "next": "^14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/node": "^20.10.6",
    "@types/react": "^18.2.46",
    "typescript": "^5.3.3",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.0.4"
  }
}

// apps/next/pages/_app.tsx
// Next.js app with tRPC provider

// apps/next/pages/index.tsx
// Main search page with SearchBar, Facets, and ResultCard

// apps/next/trpc/client.ts
// tRPC client configuration pointing to http://localhost:8000/trpc

// apps/next/components/search/SearchBar.tsx
// Search input with submit button

// apps/next/components/search/Facets.tsx
// Filters for source (papers/startups) and year_gte

// apps/next/components/search/ResultCard.tsx
// Display individual search result with:
// - Title, source badge, snippet
// - why_this_result bullets
// - Metadata (year, venue, concepts, etc.)
// - Summarize button

// apps/next/hooks/useSearch.ts
// tRPC mutation hook for search

// apps/next/hooks/useSummarize.ts
// tRPC mutation hook for summarize

// apps/next/tailwind.config.ts
// Tailwind configuration

// apps/next/tsconfig.json
// TypeScript configuration extending ../../tsconfig.base.json

// apps/next/next.config.js
// Next.js configuration
```

**Implementation requirements**:
- Use Next.js 14 App Router (pages/ directory, not app/ directory for this version)
- tRPC client connects to backend/api
- Search page with real-time search (debounced)
- Faceted filtering client-side
- Result cards with expandable summaries
- Save list functionality (in-memory state)
- Responsive design with Tailwind
- Loading states and error handling

### PHASE 3: Docker & Orchestration

**Create these files**:

```yaml
# docker-compose.yml (at repo root)
version: '3.9'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: r2d
      POSTGRES_USER: r2d
      POSTGRES_PASSWORD: r2d
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  opensearch:
    image: opensearchproject/opensearch:2.13.0
    environment:
      - discovery.type=single-node
      - DISABLE_SECURITY_PLUGIN=true
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - opensearch_data:/usr/share/opensearch/data

  prisma-migrations:
    build:
      context: .
      dockerfile: packages/prisma/Dockerfile
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://r2d:r2d@postgres:5432/r2d

  llama-indexer:
    build:
      context: ./backend/llama-indexer
      dockerfile: Dockerfile
    ports:
      - "8002:8002"
    depends_on:
      - postgres
      - opensearch
    environment:
      - DATABASE_URL=postgresql://r2d:r2d@postgres:5432/r2d
      - OPENSEARCH_HOST=opensearch
      - OPENSEARCH_PORT=9200
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_INDEX_NAME=r2d-chunks
      - EMBEDDING_MODEL=intfloat/e5-base-v2
    env_file:
      - .env

  litellm:
    build:
      context: ./backend/litellm
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - COHERE_API_KEY=${COHERE_API_KEY}
    env_file:
      - .env

  api:
    build:
      context: ./backend/api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - litellm
      - llama-indexer
    environment:
      - DATABASE_URL=postgresql://r2d:r2d@postgres:5432/r2d
      - LITELLM_URL=http://litellm:8001
      - LLAMA_INDEXER_URL=http://llama-indexer:8002
      - ADMIN_BEARER_TOKEN=${ADMIN_BEARER_TOKEN}
    env_file:
      - .env

  next:
    build:
      context: ./apps/next
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - api
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

volumes:
  postgres_data:
  opensearch_data:
```

**Create Dockerfiles**:

```dockerfile
# backend/api/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json yarn.lock ./
COPY packages/prisma packages/prisma
COPY packages/universal packages/universal
COPY backend/api backend/api
RUN yarn install --frozen-lockfile
RUN yarn workspace @r2d/api build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/backend/api/dist ./dist
COPY --from=builder /app/backend/api/package.json ./
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 8000
CMD ["node", "dist/index.js"]

# backend/litellm/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]

# backend/llama-indexer/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

# apps/next/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json yarn.lock ./
COPY packages packages
COPY apps/next apps/next
RUN yarn install --frozen-lockfile
RUN yarn workspace @r2d/next build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/apps/next/.next ./.next
COPY --from=builder /app/apps/next/public ./public
COPY --from=builder /app/apps/next/package.json ./
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["yarn", "start"]

# packages/prisma/Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json yarn.lock ./
COPY packages/prisma packages/prisma
RUN yarn install --frozen-lockfile
RUN yarn workspace @r2d/prisma db:generate
CMD ["yarn", "workspace", "@r2d/prisma", "db:push"]
```

### PHASE 4: Data & Scripts

**Create these files**:

```yaml
# data/startups_seed.yaml
materials_science:
  - "promising materials science startups 2023-2024"
  - "advanced materials companies battery technology"
  - "solid-state battery startups"
  - "graphene materials companies"
  - "nanomaterials startups"

biotechnology:
  - "biotech startups CRISPR gene editing"
  - "synthetic biology companies"
  - "protein engineering startups"
  - "cell therapy companies"
  - "mRNA therapeutic startups"

battery:
  - "next-generation battery startups"
  - "lithium-ion battery improvements"
  - "solid electrolyte companies"
  - "battery recycling startups"
  - "fast-charging battery technology"

machine_learning:
  - "AI infrastructure startups 2024"
  - "machine learning operations MLOps"
  - "large language model companies"
  - "AI chip startups"
  - "machine learning for drug discovery"
```

```jsonl
// data/eval/gold_queries.jsonl
{"query": "solid electrolyte sub-zero temperature", "relevant_ids": ["paper_id_1", "paper_id_2"]}
{"query": "CRISPR gene editing bacteria", "relevant_ids": ["paper_id_3", "paper_id_4"]}
{"query": "transformer architecture improvements", "relevant_ids": ["paper_id_5", "paper_id_6"]}
{"query": "lithium-ion battery degradation", "relevant_ids": ["paper_id_7", "paper_id_8"]}
{"query": "protein folding prediction", "relevant_ids": ["paper_id_9", "paper_id_10"]}
{"query": "graphene synthesis methods", "relevant_ids": ["paper_id_11", "paper_id_12"]}
{"query": "reinforcement learning robotics", "relevant_ids": ["paper_id_13", "paper_id_14"]}
{"query": "quantum computing error correction", "relevant_ids": ["paper_id_15", "paper_id_16"]}
```

**Create CLI scripts**:

```python
# scripts/ingest_openalex.py
"""
CLI script to trigger OpenAlex ingestion via API.
Calls POST /trpc/ingest.openalex
"""

# scripts/ingest_arxiv.py
"""
CLI script to trigger arXiv ingestion via API.
Calls POST /trpc/ingest.arxiv
"""

# scripts/ingest_startups.py
"""
CLI script to trigger startup ingestion via API.
Calls POST /trpc/ingest.startups
"""

# scripts/build_indexes.py
"""
Initialize OpenSearch indices and Pinecone index.
Calls llama-indexer service endpoints.
"""

# scripts/eval_ndcg.py
"""
Evaluate search quality using nDCG@10 metric.
Tests: BM25 only, ANN only, Hybrid, Hybrid+Rerank
Reads gold_queries.jsonl and computes scores.
"""
```

### PHASE 5: Testing

**Create test files**:

```typescript
// backend/api/src/__tests__/search.test.ts
// Test tRPC search procedure

// backend/api/src/__tests__/clients.test.ts
// Test HTTP clients for Python services

// apps/next/__tests__/SearchBar.test.tsx
// Jest + RTL test for SearchBar component

// apps/next/__tests__/ResultCard.test.tsx
// Jest + RTL test for ResultCard component
```

```python
# backend/llama-indexer/tests/test_retrieval.py
"""Test hybrid retrieval, blending, and deduplication"""

# backend/llama-indexer/tests/test_api.py
"""Test FastAPI endpoints"""

# backend/litellm/tests/test_endpoints.py
"""Test rerank and summarize endpoints"""
```

### PHASE 6: Makefile & Documentation

```makefile
# Makefile
.PHONY: install dev build test clean ingest eval

install:
\tyarn install

dev:
\tdocker-compose up -d postgres opensearch
\tyarn dev

build:
\tyarn build

test:
\tyarn test

clean:
\tyarn clean
\tdocker-compose down -v

ingest:
\tpython scripts/build_indexes.py
\tpython scripts/ingest_openalex.py
\tpython scripts/ingest_arxiv.py
\tpython scripts/ingest_startups.py

eval:
\tpython scripts/eval_ndcg.py
```

**Update documentation**:

```markdown
# docs/Running_the_app_locally.md
(Complete step-by-step guide with:
- Prerequisites
- Environment setup
- .env file configuration
- Creating Pinecone index
- Running services
- Ingesting data
- Accessing the UI
- Troubleshooting)

# README.md
(High-level overview with:
- Project description
- Architecture diagram
- Quick start
- API examples
- Contributing guidelines)
```

### PHASE 7: Final Integration

**Update turbo.json** to include new services:

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env"],
  "pipeline": {
    "dev": {
      "cache": false,
      "persistent": true
    },
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "dist/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": []
    }
  }
}
```

## Acceptance Criteria

Your implementation is complete when:

1. ✅ `docker-compose up --build` starts all 6 services successfully
2. ✅ GET http://localhost:8000/trpc/admin.health returns status:"ok"
3. ✅ GET http://localhost:8001/health returns status:"ok" (litellm)
4. ✅ GET http://localhost:8002/health returns status:"ok" (llama-indexer)
5. ✅ `make ingest` successfully ingests papers and startups
6. ✅ POST to /trpc/search.search returns mixed results (papers + startups)
7. ✅ Results include non-empty why_this_result arrays
8. ✅ POST to /trpc/search.summarize returns 5-field summaries
9. ✅ `make eval` prints nDCG scores with Hybrid+Rerank >= Hybrid
10. ✅ `make test` passes all tests
11. ✅ Frontend at http://localhost:3000 displays search UI and works end-to-end

## Important Notes

- **Do not change the existing Prisma schema or universal types**
- **Maintain the exact API contracts defined in backend/api/src/routers/**
- **Python services should not import Node.js packages**
- **Use environment variables for all configuration**
- **Add comprehensive error handling and logging**
- **Follow the existing code style and patterns**

## Getting Started

1. Read ARCHITECTURE.md first to understand the system
2. Start with Phase 1 (Python service reorganization)
3. Test each service independently before integration
4. Use docker-compose to test the full system
5. Create tests as you go

---

**Ready to implement?** Start with creating `backend/litellm/server.py` and proceed phase by phase.
