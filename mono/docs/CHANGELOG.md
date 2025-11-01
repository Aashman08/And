# Changelog - Architecture Restructuring

## November 2025 - Parallel Search & Tavily Integration

### ✅ Recent Changes

#### 1. Tavily Web Search Integration
- **Created** `backend/tavily/` - New Python service for real-time web search
  - FastAPI server with `/search` and `/extract` endpoints
  - Tavily API integration for startup discovery
  - Port 8003
- **Replaced** Perplexity with Tavily for web search
  - Removed automated startup seed query discovery
  - Using real-time web search instead

#### 2. Parallel Search Architecture
- **Updated** `backend/api/src/procedures/search.ts` - Parallel execution
  - Calls Tavily + Database simultaneously
  - Returns separate `startups` and `papers` arrays
- **Created** `backend/api/src/clients/tavily.ts` - Tavily client
- **Updated** Frontend to display two sections:
  - 🏢 Relevant Startups (top 10 from web)
  - 📄 Research Papers (top 20 from database)

#### 3. Service Separation & Clean Architecture
- **Moved** Cohere reranking from LiteLLM to Llama-Indexer
- **Simplified** LiteLLM to ONLY handle summarization
- **Created** `prompts.py` and `constants.py` in each service
- **Removed** automated startup ingestion (seed queries)

#### 4. Bug Fixes
- **Fixed** `.storybook/preview.ts` → `.tsx` (JSX support)
- **Fixed** `ResultCard.tsx` corrupted `'use client'` directive
- **Fixed** `docker-compose.yml` corrupted version string
- **Fixed** Llama-Indexer module imports (`app.main` → `main`)
- **Added** React import to Storybook preview

---

## January 2025 - Major Architecture Refactor

### ✅ Completed Changes

#### 1. Backend Services Layer Added
- **Created** `backend/api/src/services/` - New layer for Prisma database operations
  - `DocumentService` - CRUD operations for documents
  - `ChunkService` - CRUD operations for chunks
  - `IngestionService` - Ingestion run tracking
- **Updated** procedures to use services layer instead of direct Prisma calls
- **Created** `docs/ARCHITECTURE_LAYERS.md` - Complete guide on layered architecture

#### 2. Python Microservices Reorganized
- **Moved** all Python code from `backend-temp/` to proper microservices
- **Created** `backend/litellm/` - LiteLLM proxy service
  - FastAPI server with `/rerank` and `/summarize` endpoints
  - Custom implementations in `custom/` directory
  - Complete `requirements.txt` and `package.json`
- **Created** `backend/llama-indexer/` - Document processing service
  - FastAPI server with search, indexing, and ingestion endpoints
  - Services: embeddings, chunking, retriever, highlight
  - Clients: opensearch, pinecone
  - Complete `requirements.txt` and `package.json`
- **Removed** `backend-temp/` directory

#### 3. Documentation Reorganization
- **Moved** all `.md` files to `docs/` directory except `README.md`
- **Updated** `docs/ARCHITECTURE.md` with:
  - New services layer in backend/api
  - Updated "What's Been Implemented" section
  - Current state of all microservices
  - Reference to ARCHITECTURE_LAYERS.md
- **Updated** `README.md` with links to docs folder

#### 4. Architecture Pattern Established
- **Implemented** clean layered architecture in `backend/api/`:
  ```
  routers/ → procedures/ → services/ + clients/
  ```
- **Documented** layer responsibilities and anti-patterns
- **Created** example code showing correct patterns

### 📁 Current Structure

```
mono/
├── README.md (root documentation)
├── docs/                              ← All .md files here
│   ├── ARCHITECTURE.md               ← System design
│   ├── ARCHITECTURE_LAYERS.md        ← Backend API layers
│   ├── Running_the_app_locally.md    ← Setup guide
│   ├── IMPLEMENTATION_PROMPT.md      ← Completion guide
│   └── IMPLEMENTATION_SUMMARY.md     ← Summary
│
├── backend/                           ← At root level
│   ├── api/                           ← TypeScript/tRPC
│   │   └── src/
│   │       ├── routers/              ← tRPC endpoints
│   │       ├── procedures/           ← Business logic
│   │       ├── services/             ← ⭐ NEW - Prisma operations
│   │       └── clients/              ← External HTTP calls
│   │
│   ├── litellm/                      ← ⭐ COMPLETE - Python LLM service
│   │   ├── server.py
│   │   ├── custom/
│   │   └── requirements.txt
│   │
│   └── llama-indexer/                ← ⭐ COMPLETE - Python search service
│       ├── app/main.py
│       ├── app/services/
│       ├── app/clients/
│       └── requirements.txt
│
├── apps/next/                         ← Frontend (to be implemented)
├── packages/                          ← Shared packages
│   ├── prisma/
│   └── universal/
└── data/                              ← Seed data (complete)
```

### 🎯 Key Improvements

1. **Separation of Concerns**: Clear boundaries between layers
2. **Testability**: Easy to mock services and clients
3. **Reusability**: Services can be shared across procedures
4. **Maintainability**: Changes isolated to appropriate layers
5. **Type Safety**: End-to-end TypeScript types

### 📚 Architecture Patterns

#### Correct Pattern ✅
```typescript
// In procedures/summarize.ts
const documentService = new DocumentService(ctx.prisma);
const docs = await documentService.getByIds(input.ids);
const summaries = await litellmClient.summarizeBatch(docs);
```

#### Anti-Pattern ❌
```typescript
// DON'T do this in procedures
const docs = await ctx.prisma.document.findMany({ ... });
const response = await axios.post('http://localhost:8001/summarize', ...);
```

### 🚀 Ready to Run

All backend services are complete and can be started with:
```bash
yarn dev
```

Services will run on:
- TypeScript API: http://localhost:8000
- LiteLLM: http://localhost:8001
- Llama-Indexer: http://localhost:8002
- Tavily: http://localhost:8003

### 📋 Remaining Work

See `docs/ARCHITECTURE.md` section "What Still Needs Implementation" for:
1. Frontend (apps/next/)
2. Docker orchestration
3. Dockerfiles
4. CLI scripts
5. Tests

---

**Date**: January 2025
**Status**: Backend microservices complete ✅
