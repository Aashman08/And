# R&D Discovery System - Architecture Guide

## 🏗️ System Architecture

This is a **microservices-based R&D discovery platform** with a hybrid architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js 14)                   │
│                      apps/next/ (TypeScript)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ tRPC
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (TypeScript/tRPC)                │
│                        backend/api/                             │
│  - Routes requests to specialized Python services              │
│  - Handles auth, orchestration, and business logic             │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                  │
           ▼                                  ▼
┌──────────────────────────┐    ┌────────────────────────────────┐
│   LiteLLM Proxy Service  │    │  Llama-Indexer Service         │
│   backend/litellm/       │    │  backend/llama-indexer/        │
│   (Python)               │    │  (Python)                      │
│                          │    │                                │
│  - OpenAI summarization  │    │  - Document chunking           │
│  - Cohere reranking      │    │  - Embedding (e5-base-v2)      │
│  - Unified LLM interface │    │  - OpenSearch (BM25)           │
│                          │    │  - Pinecone (vectors)          │
│                          │    │  - Hybrid search & highlights  │
└──────────────────────────┘    └────────────────────────────────┘
           │                                  │
           └──────────────┬───────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  - PostgreSQL (metadata via Prisma)                            │
│  - OpenSearch (BM25 full-text search)                          │
│  - Pinecone Serverless (vector similarity)                     │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Repository Structure

```
mono/
├── apps/
│   └── next/                          # Next.js 14 frontend (TypeScript)
│       ├── components/                # React components
│       ├── pages/                     # Next.js routes
│       ├── hooks/                     # Custom React hooks
│       ├── trpc/                      # tRPC client setup
│       ├── types/                     # TypeScript type definitions
│       └── utils/                     # Utility functions
│
├── backend/                           # ⚠️ At ROOT level, not under apps/
│   ├── api/                           # Main API gateway (TypeScript/tRPC)
│   │   ├── src/
│   │   │   ├── routers/              # tRPC routers (search, ingest, admin)
│   │   │   ├── procedures/           # Business logic orchestration
│   │   │   ├── services/             # ⭐ Database operations (Prisma)
│   │   │   ├── clients/              # HTTP clients for Python services
│   │   │   ├── utils/                # Logger, helpers
│   │   │   ├── context.ts            # tRPC context
│   │   │   ├── trpc.ts               # tRPC initialization
│   │   │   └── index.ts              # Express server + tRPC
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── litellm/                       # LiteLLM proxy (Python)
│   │   ├── custom/                    # Custom LiteLLM implementations
│   │   ├── config.yaml                # LiteLLM configuration
│   │   ├── requirements.txt
│   │   └── server.py                  # FastAPI endpoints for LLM ops
│   │
│   └── llama-indexer/                 # Document processing (Python)
│       ├── app/
│       │   ├── services/              # Chunking, embedding, search
│       │   ├── clients/               # OpenSearch, Pinecone clients
│       │   └── main.py                # FastAPI server
│       └── requirements.txt
│
├── packages/                          # Shared libraries
│   ├── prisma/                        # Database schema and client
│   │   ├── schema.prisma
│   │   ├── src/client.ts
│   │   └── migrations/
│   │
│   ├── universal/                     # Shared types and constants
│   │   └── src/
│   │       ├── types.ts
│   │       └── constants.ts
│   │
│   └── node-utils/                    # Node.js utilities (TODO)
│       └── src/
│
├── data/                              # Seed data and evaluation
│   ├── startups_seed.yaml
│
├── docs/                              # Documentation
│   ├── Running_the_app_locally.md
│   └── ARCHITECTURE.md                # This file
│
├── scripts/                           # Utility scripts
│   ├── ingest_openalex.py
│   ├── ingest_arxiv.py
│   ├── ingest_startups.py
│   └── build_indexes.py
│
└── [Root Configuration]
    ├── package.json                   # Yarn workspaces root
    ├── turbo.json                     # Turborepo config
    ├── docker-compose.yml             # Multi-service orchestration
    └── .env                           # Environment variables
```

## 🔑 Key Architectural Decisions

### 1. **Polyglot Microservices**
- **TypeScript (backend/api)**: API gateway, orchestration, business logic
- **Python (backend/litellm)**: LLM operations (reranking, summarization)
- **Python (backend/llama-indexer)**: Document processing, search, embeddings

**Why?**
- TypeScript for type-safe API and frontend integration
- Python for ML libraries (sentence-transformers, LlamaIndex)
- Each service has a single responsibility

### 2. **tRPC Instead of REST**
- Type-safe end-to-end from backend to frontend
- Auto-generated types from procedures
- Better DX with autocomplete and compile-time checks

### 3. **Service Boundaries**
- **backend/api**: Thin orchestration layer, no ML/heavy compute
- **backend/litellm**: All LLM API calls isolated (OpenAI, Cohere)
- **backend/llama-indexer**: All search/indexing/embedding logic

### 4. **Layered Architecture in backend/api/**

The TypeScript API gateway follows a clean **layered architecture**:

```
routers/ (tRPC endpoints)
    ↓ validates input
procedures/ (business logic orchestration)
    ↓ calls services + clients
    ├─→ services/ (Prisma database operations)
    └─→ clients/ (external HTTP to Python services)
```

**Layer Responsibilities**:

| Layer | Purpose | Example |
|-------|---------|---------|
| **routers/** | Define tRPC routes, validate input with Zod | `routers/search.ts` |
| **procedures/** | Orchestrate business logic, call services & clients | `procedures/summarize.ts` |
| **services/** | Direct Prisma database operations ONLY | `services/documents.ts` |
| **clients/** | External HTTP API calls ONLY | `clients/litellm.ts` |

**Key Rules**:
- ✅ Procedures orchestrate (call services + clients)
- ✅ Services handle Prisma database operations
- ✅ Clients handle external HTTP calls
- ❌ Never put Prisma queries directly in procedures
- ❌ Never make HTTP calls directly in procedures

**Example Flow**:
```typescript
// ✅ CORRECT - Layered architecture
async function summarizeProcedure(input, ctx) {
  // Use service for database
  const documentService = new DocumentService(ctx.prisma);
  const docs = await documentService.getByIds(input.ids);

  // Use client for external API
  const summaries = await litellmClient.summarizeBatch(docs);

  return { summaries };
}
```

See [ARCHITECTURE_LAYERS.md](./ARCHITECTURE_LAYERS.md) for complete details.

### 5. **Shared Database, Separate Indexes**
- PostgreSQL (Prisma): Source of truth for documents
- OpenSearch: Fast BM25 full-text search
- Pinecone: Vector similarity search

## ✅ What's Been Implemented

### Infrastructure
- ✅ Monorepo structure (Turborepo + Yarn workspaces)
- ✅ Shared packages: @r2d/prisma, @r2d/universal
- ✅ TypeScript configuration with project references

### Backend API (backend/api/)
- ✅ tRPC server with Express
- ✅ Context, middleware, and auth
- ✅ Routers: search, ingest, admin
- ✅ Procedures: search, summarize, ingest orchestration
- ✅ **Services (NEW)**: DocumentService, ChunkService, IngestionService
- ✅ Clients: litellmClient, llamaIndexerClient
- ✅ Logging with Winston
- ✅ Layered architecture pattern implemented

### LiteLLM Service (backend/litellm/)
- ✅ FastAPI server with endpoints
- ✅ POST /rerank - Cohere Rerank v3 integration
- ✅ POST /summarize - OpenAI GPT-4o-mini summaries
- ✅ GET /health - Health check
- ✅ Custom implementations in custom/ directory
- ✅ Full requirements.txt

### Llama-Indexer Service (backend/llama-indexer/)
- ✅ FastAPI server with endpoints
- ✅ POST /search/hybrid - BM25 + vector hybrid search
- ✅ POST /highlights - Highlight generation
- ✅ POST /index - Document indexing
- ✅ POST /ingest/* - OpenAlex, arXiv, Startup ingestion
- ✅ GET /health - Health check with Pinecone stats
- ✅ Services: embeddings, chunking, retriever, highlight
- ✅ Clients: opensearch, pinecone
- ✅ Full requirements.txt

## ⚠️ What Still Needs Implementation

All backend microservices are complete and properly structured! Remaining work:

### 1. Frontend (apps/next/)

Expand structure to include:
```
apps/next/
├── components/
│   ├── search/
│   │   ├── SearchBar.tsx
│   │   ├── Facets.tsx
│   │   └── ResultCard.tsx
│   └── layout/
├── pages/
│   ├── _app.tsx
│   ├── index.tsx          # Main search page
│   └── api/
│       └── trpc/[trpc].ts  # tRPC handler
├── trpc/
│   └── client.ts          # tRPC client setup
├── hooks/
│   ├── useSearch.ts
│   └── useSummarize.ts
├── types/
├── utils/
├── styles/
│   └── globals.css
├── package.json
├── tsconfig.json
├── next.config.js
└── tailwind.config.ts
```

### 2. Docker Orchestration

Create `docker-compose.yml` with all services:
```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: r2d
      POSTGRES_USER: r2d
      POSTGRES_PASSWORD: r2d
    ports:
      - "5432:5432"

  opensearch:
    image: opensearchproject/opensearch:2.13.0
    environment:
      - discovery.type=single-node
      - DISABLE_SECURITY_PLUGIN=true
    ports:
      - "9200:9200"

  api:
    build: ./backend/api
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

  litellm:
    build: ./backend/litellm
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - COHERE_API_KEY=${COHERE_API_KEY}

  llama-indexer:
    build: ./backend/llama-indexer
    ports:
      - "8002:8002"
    depends_on:
      - postgres
      - opensearch
    environment:
      - DATABASE_URL=postgresql://r2d:r2d@postgres:5432/r2d
      - OPENSEARCH_HOST=opensearch
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - EMBEDDING_MODEL=intfloat/e5-base-v2

  next:
    build: ./apps/next
    ports:
      - "3000:3000"
    depends_on:
      - api
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Dockerfiles

Create Dockerfiles for each service:

**backend/api/Dockerfile**:
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile
COPY . .
RUN yarn build
EXPOSE 8000
CMD ["node", "dist/index.js"]
```

**backend/litellm/Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

**backend/llama-indexer/Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### 4. CLI Scripts

Create Python scripts in `scripts/`:
- `ingest_openalex.py` - Trigger OpenAlex ingestion via API
- `ingest_arxiv.py` - Trigger arXiv ingestion via API
- `ingest_startups.py` - Trigger startup ingestion via API
- `build_indexes.py` - Initialize OpenSearch and Pinecone indices
- `eval_ndcg.py` - Evaluate search quality with nDCG@10 metric

### 5. Testing

- Backend API tests (Jest for TypeScript)
- Python service tests (pytest for litellm, llama-indexer)
- Frontend tests (Jest + React Testing Library)
- Integration tests
- E2E tests (Playwright - optional)

## 🚀 Getting Started

1. **Install dependencies**:
   ```bash
   yarn install
   ```

2. **Start infrastructure**:
   ```bash
   docker-compose up -d postgres opensearch
   ```

3. **Run Prisma migrations**:
   ```bash
   yarn workspace @r2d/prisma db:push
   ```

4. **Start all services**:
   ```bash
   yarn dev  # Uses Turborepo to start all services
   ```

5. **Ingest data**:
   ```bash
   curl -X POST http://localhost:8000/trpc/ingest.openalex \\
     -H "Authorization: Bearer dev-admin-token"
   ```

6. **Search**:
   ```bash
   curl -X POST http://localhost:8000/trpc/search.search \\
     -H "Content-Type: application/json" \\
     -d '{"query": "solid electrolyte batteries"}'
   ```

## 📚 Additional Resources

### Internal Documentation
- **[ARCHITECTURE_LAYERS.md](./ARCHITECTURE_LAYERS.md)** - Detailed layered architecture guide for backend/api/
- **[Running_the_app_locally.md](./Running_the_app_locally.md)** - Complete setup and troubleshooting guide
- **[IMPLEMENTATION_PROMPT.md](./IMPLEMENTATION_PROMPT.md)** - Guide for completing remaining components

### External Documentation
- [tRPC Documentation](https://trpc.io/) - End-to-end typesafe APIs
- [LiteLLM Documentation](https://docs.litellm.ai/) - Unified LLM interface
- [Pinecone Serverless](https://docs.pinecone.io/guides/getting-started/quickstart) - Vector database
- [OpenSearch Documentation](https://opensearch.org/docs/latest/) - Search and analytics
- [Prisma Documentation](https://www.prisma.io/docs) - TypeScript ORM
- [Sentence Transformers](https://www.sbert.net/) - Embeddings library

---

**Last Updated**: January 2025
**Maintainers**: R&D Discovery Team
