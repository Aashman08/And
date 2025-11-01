# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**R&D Discovery System** - AI-powered platform that searches web for startups (Tavily) and database for papers (hybrid search), displaying results in separate sections with LLM-powered summaries.

**Tech Stack**:
- Frontend: Next.js 14 (TypeScript)
- API Gateway: tRPC + Express (TypeScript)
- Microservices: Python (FastAPI)
- Database: PostgreSQL + Prisma ORM
- Search: OpenSearch (BM25) + Pinecone (vectors) + Tavily (web)
- ML: sentence-transformers (e5-base-v2), OpenAI, Cohere

## Architecture

This is a **microservices monorepo** with four main services:

1. **backend/api/** - TypeScript/tRPC API gateway (port 8000)
2. **backend/litellm/** - Python summarization service (port 8001)
3. **backend/llama-indexer/** - Python search/reranking service (port 8002)
4. **backend/tavily/** - Python web search service (port 8003)

### Critical: Layered Architecture in backend/api/

The TypeScript API gateway follows a strict **4-layer pattern**:

```
routers/     → tRPC endpoints (input validation with Zod)
procedures/  → Business logic orchestration
services/    → Prisma database operations ONLY
clients/     → External HTTP API calls ONLY
```

**MUST FOLLOW THESE RULES**:
- ✅ Procedures orchestrate by calling services + clients
- ✅ Services contain ONLY Prisma database operations
- ✅ Clients contain ONLY external HTTP calls (axios)
- ❌ NEVER put Prisma queries directly in procedures
- ❌ NEVER make HTTP calls directly in procedures

**Correct Pattern**:
```typescript
// procedures/summarize.ts
const documentService = new DocumentService(ctx.prisma);
const docs = await documentService.getByIds(input.ids);
const summaries = await litellmClient.summarizeBatch(docs);
```

**Wrong Pattern**:
```typescript
// ❌ DON'T DO THIS
const docs = await ctx.prisma.document.findMany({ ... });
const response = await axios.post('http://localhost:8001/summarize', ...);
```

See `docs/ARCHITECTURE_LAYERS.md` for complete details.

## Essential Commands

### Installation
```bash
yarn install                    # Install all dependencies (root + workspaces)
```

### Development
```bash
yarn dev                        # Start all services with Turborepo
yarn workspace @r2d/api dev     # Run TypeScript API only
yarn workspace @r2d/next dev    # Run frontend only

# Python services (from their directories)
cd backend/litellm && python -m uvicorn server:app --reload --port 8001
cd backend/llama-indexer && python -m uvicorn main:app --reload --port 8002
cd backend/tavily && python -m uvicorn server:app --reload --port 8003
```

### Database
```bash
yarn workspace @r2d/prisma db:generate  # Generate Prisma client
yarn workspace @r2d/prisma db:push      # Push schema to database
yarn workspace @r2d/prisma db:studio    # Open Prisma Studio
```

### Building
```bash
yarn build                      # Build all packages with Turborepo
yarn workspace @r2d/api build   # Build TypeScript API only
```

### Testing
```bash
yarn test                       # Run all tests
yarn workspace @r2d/api test    # Test TypeScript API
cd backend/litellm && pytest    # Test LiteLLM service
cd backend/llama-indexer && pytest  # Test Llama-Indexer service
```

### Type Checking & Linting
```bash
yarn type-check                 # Type check all TypeScript
yarn lint                       # Lint all code
```

### Docker
```bash
docker-compose up -d postgres opensearch    # Start infrastructure only
docker-compose up --build                   # Start all services with Docker
docker-compose down -v                      # Stop and clean everything
```

## Data Models

The system uses **three main Prisma models**:

1. **Document** - Papers or startups (source: PAPER | STARTUP)
   - Common: id, externalId, title, description, year
   - Papers: doi, authors, venue, concepts
   - Startups: website, oneLiner, stage, industry, country

2. **Chunk** - Semantic chunks for retrieval
   - Links to Document via documentId
   - Has chunkIndex, text, section, vectorId (Pinecone reference)

3. **IngestionRun** - Tracks ingestion jobs
   - Status: PENDING | IN_PROGRESS | COMPLETED | FAILED
   - Stats: totalFetched, totalProcessed, totalIndexed, errorCount

## Service Communication

**backend/api** communicates with Python services via HTTP:

- **litellmClient** (`backend/api/src/clients/litellm.ts`)
  - POST /rerank - Cohere Rerank v3
  - POST /summarize - OpenAI GPT-4o-mini summaries
  - GET /health

- **llamaIndexerClient** (`backend/api/src/clients/llama-indexer.ts`)
  - POST /search/hybrid - BM25 + vector hybrid search
  - POST /highlights - Generate "why this result?" explanations
  - POST /index - Index documents to OpenSearch + Pinecone
  - POST /ingest/* - Trigger ingestion from OpenAlex, arXiv, Perplexity
  - GET /health

## Adding New Features

### Adding a New API Endpoint

1. **Define schema** in `backend/api/src/routers/[name].ts`
   ```typescript
   const myRequestSchema = z.object({ ... });
   ```

2. **Create service** if database access needed in `backend/api/src/services/[name].ts`
   ```typescript
   export class MyService {
     constructor(private prisma: PrismaClient) {}
     async myOperation() { return this.prisma.model.findMany(...); }
   }
   ```

3. **Create procedure** in `backend/api/src/procedures/[name].ts`
   ```typescript
   export async function myProcedure(input, ctx) {
     const service = new MyService(ctx.prisma);
     const data = await service.myOperation();
     return data;
   }
   ```

4. **Add router** in `backend/api/src/routers/[name].ts`
   ```typescript
   export const myRouter = router({
     myEndpoint: publicProcedure
       .input(myRequestSchema)
       .mutation(async ({ input, ctx }) => myProcedure(input, ctx)),
   });
   ```

5. **Register router** in `backend/api/src/routers/index.ts`

### Modifying Database Schema

1. Edit `packages/prisma/schema.prisma`
2. Run `yarn workspace @r2d/prisma db:push`
3. The Prisma client auto-regenerates
4. Update services in `backend/api/src/services/` as needed

### Adding Python Service Functionality

**For LiteLLM** (`backend/litellm/`):
- Add endpoint to `server.py`
- Implement in `custom/` directory
- Update `requirements.txt` if new deps needed

**For Llama-Indexer** (`backend/llama-indexer/`):
- Add endpoint to `main.py`
- Implement in `services/` (business logic) or `clients/` (external APIs)
- Update `requirements.txt` if new deps needed

**For Tavily** (`backend/tavily/`):
- Add endpoint to `server.py`
- Implement in `services/` directory
- Update `requirements.txt` if new deps needed

## Environment Setup

Required API keys in `.env`:
- `OPENAI_API_KEY` - For summarization (GPT-4o-mini)
- `COHERE_API_KEY` - For reranking (Rerank v3)
- `PINECONE_API_KEY` - For vector storage
- `TAVILY_API_KEY` - For real-time web search (startups)
- `ADMIN_BEARER_TOKEN` - For protected admin endpoints

**Important**: You must manually create the Pinecone serverless index:
- Name: `r2d-chunks`
- Dimensions: 768 (for e5-base-v2)
- Metric: cosine
- Cloud: AWS, Region: us-west-2

## Search Workflow (Current Implementation)

**User Query Flow:**
```
1. User types query: "how to overcome anode plating"
   ↓
2. Frontend → API Gateway (/search.query)
   ↓
3. API Gateway → PARALLEL execution:
   ├─→ Tavily Service (port 8003)
   │   └─ Web search → Top 10 startups
   │
   └─→ Llama-Indexer Service (port 8002)
       ├─ Hybrid search (BM25 + vector) → 256 results
       ├─ Rerank with Cohere → Top 20 papers
       └─ Generate highlights
   ↓
4. Return to Frontend:
   {
     startups: [...10 from Tavily],
     papers: [...20 from database]
   }
   ↓
5. Frontend displays TWO SEPARATE SECTIONS:
   - 🏢 Relevant Startups (10)
   - 📄 Research Papers (20)
```

**User Clicks Summarize:**
```
1. Frontend → API Gateway (/search.summarize)
   ↓
2. API Gateway → PostgreSQL (get document)
   ↓
3. API Gateway → LiteLLM Service (port 8001)
   ↓
4. LiteLLM → OpenAI GPT-4o-mini
   ↓
5. Returns 5-section summary:
   - problem
   - approach
   - evidence_or_signals
   - result
   - limitations
```

## Common Issues

**"Prisma Client not found"**:
```bash
yarn workspace @r2d/prisma db:generate
```

**"Port already in use"**:
```bash
lsof -ti:8000 | xargs kill -9  # Replace 8000 with your port
```

**"Module not found" in Python services**:
```bash
cd backend/[service] && pip install -r requirements.txt
```

**Type errors after schema change**:
```bash
yarn workspace @r2d/prisma db:generate
yarn type-check
```

## Documentation

- `docs/ARCHITECTURE.md` - System design and microservices overview
- `docs/ARCHITECTURE_LAYERS.md` - Backend API layered architecture (CRITICAL)
- `docs/Running_the_app_locally.md` - Complete setup guide with troubleshooting
- `docs/IMPLEMENTATION_PROMPT.md` - Guide for completing remaining features
- `docs/CHANGELOG.md` - Recent architecture changes

## Key Conventions

1. **TypeScript API** uses class-based services with Prisma injected via constructor
2. **Python services** use FastAPI with async/await patterns
3. **Error handling**: TRPCError in procedures, HTTPException in Python services
4. **Logging**: Winston in TypeScript, Python logging module in services
5. **No direct Prisma in procedures** - always use service layer
6. **No direct HTTP in procedures** - always use client layer
7. **Workspace references**: Use `@r2d/prisma`, `@r2d/universal` for imports

## Testing Patterns

**TypeScript API**:
- Mock services and clients in procedure tests
- Use Jest with TypeScript
- Test files: `*.test.ts`

**Python services**:
- Use pytest with async support
- Mock external APIs (OpenAI, Cohere, Pinecone)
- Test files: `test_*.py`

**Integration tests**:
- Start services with docker-compose
- Test full request flow through API gateway

---

**When in doubt**: Read `docs/ARCHITECTURE_LAYERS.md` - it contains the critical layered architecture pattern that MUST be followed in backend/api/.

NOTE - Do not create new .md files please, it is stupid
