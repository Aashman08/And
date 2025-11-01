# Backend API Architecture Layers

## Overview

The TypeScript/tRPC API gateway follows a **layered architecture** pattern for clean separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                      routers/                           │
│                  (tRPC Endpoints)                       │
│  - Defines API routes and input validation             │
│  - Calls procedures with validated input               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   procedures/                           │
│              (Business Logic Layer)                     │
│  - Orchestrates business logic                         │
│  - Calls services for database operations              │
│  - Calls clients for external API calls                │
│  - Combines results and handles errors                 │
└────────┬──────────────────────────────────┬─────────────┘
         │                                  │
         ▼                                  ▼
┌──────────────────────┐        ┌──────────────────────┐
│     services/        │        │      clients/        │
│  (Data Access Layer) │        │  (External APIs)     │
│                      │        │                      │
│ - DocumentService    │        │ - litellmClient      │
│ - ChunkService       │        │ - llamaIndexerClient │
│ - IngestionService   │        │                      │
│                      │        │                      │
│ Uses: Prisma (DB)    │        │ Uses: axios (HTTP)   │
└──────────────────────┘        └──────────────────────┘
```

## Layer Responsibilities

### 1. Routers (`src/routers/`)

**Purpose**: Define tRPC API routes and input validation

**Example**: `src/routers/search.ts`
```typescript
export const searchRouter = router({
  search: publicProcedure
    .input(searchRequestSchema)      // ← Zod validation
    .mutation(async ({ input, ctx }) => {
      return searchProcedure(input, ctx);  // ← Call procedure
    }),
});
```

**Key Points**:
- Uses Zod schemas for input validation
- No business logic here
- Simply routes to appropriate procedure

### 2. Procedures (`src/procedures/`)

**Purpose**: Orchestrate business logic by coordinating services and clients

**Example**: `src/procedures/summarize.ts`
```typescript
export async function summarizeProcedure(input: SummarizeInput, ctx: Context) {
  // 1. Fetch from database using service
  const documentService = new DocumentService(ctx.prisma);
  const documents = await documentService.getByIds(input.ids);

  // 2. Call external LiteLLM service using client
  const summaries = await litellmClient.summarizeBatch(documents);

  // 3. Return combined result
  return { summaries };
}
```

**Key Points**:
- Contains business logic
- Calls **services** for database operations
- Calls **clients** for external API calls
- Handles errors and transformations
- No direct Prisma queries (delegates to services)
- No direct HTTP calls (delegates to clients)

### 3. Services (`src/services/`)

**Purpose**: Direct Prisma database operations (data access layer)

**Example**: `src/services/documents.ts`
```typescript
export class DocumentService {
  constructor(private prisma: PrismaClient) {}

  async getByIds(ids: string[]): Promise<Document[]> {
    return this.prisma.document.findMany({
      where: { id: { in: ids } },
      include: { chunks: true },
    });
  }

  async create(data: CreateDocumentInput): Promise<Document> {
    return this.prisma.document.create({ data });
  }
}
```

**Key Points**:
- Only Prisma database operations
- No external API calls
- Reusable across procedures
- Takes `PrismaClient` in constructor
- Returns raw Prisma models

**Available Services**:
- `DocumentService` - CRUD for documents
- `ChunkService` - CRUD for chunks
- `IngestionService` - Track ingestion runs

### 4. Clients (`src/clients/`)

**Purpose**: HTTP clients for calling external Python services

**Example**: `src/clients/litellm.ts`
```typescript
export class LiteLLMClient {
  private client: AxiosInstance;

  async summarizeBatch(documents: any[]): Promise<any> {
    const response = await this.client.post('/summarize', { documents });
    return response.data.summaries;
  }
}

export const litellmClient = new LiteLLMClient();
```

**Key Points**:
- Only HTTP calls to external services
- No database operations
- No business logic
- Uses axios for HTTP
- Singleton pattern (exported instance)

**Available Clients**:
- `litellmClient` - Calls LiteLLM service (port 8001)
- `llamaIndexerClient` - Calls Llama-Indexer service (port 8002)

## Example: Full Request Flow

**User Request**: `POST /trpc/search.summarize { ids: ["doc1", "doc2"] }`

### Flow:

```
1. Router (src/routers/search.ts)
   ↓ Validates input with Zod schema
   ↓ Passes to procedure

2. Procedure (src/procedures/summarize.ts)
   ↓ Creates DocumentService
   ↓ Calls documentService.getByIds(ids)

3. Service (src/services/documents.ts)
   ↓ Executes Prisma query
   ↓ Returns documents from database

4. Procedure (continued)
   ↓ Takes documents
   ↓ Calls litellmClient.summarizeBatch(documents)

5. Client (src/clients/litellm.ts)
   ↓ Makes HTTP POST to http://localhost:8001/summarize
   ↓ Returns summaries from LiteLLM service

6. Procedure (continued)
   ↓ Combines results
   ↓ Returns to router

7. Router
   ↓ Returns to tRPC
   ↓ Sends response to user
```

## Why This Architecture?

### ✅ Benefits

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Testability**: Easy to mock services and clients in tests
3. **Reusability**: Services can be used by multiple procedures
4. **Maintainability**: Changes to database schema only affect services
5. **Type Safety**: TypeScript types flow through all layers

### Example: Adding a New Feature

**Task**: Add ability to search documents by title

**Changes needed**:

1. **Service** (`services/documents.ts`):
```typescript
async searchByTitle(title: string): Promise<Document[]> {
  return this.prisma.document.findMany({
    where: { title: { contains: title, mode: 'insensitive' } },
  });
}
```

2. **Procedure** (`procedures/search.ts`):
```typescript
const documentService = new DocumentService(ctx.prisma);
const results = await documentService.searchByTitle(input.title);
```

3. **Router** (`routers/search.ts`):
```typescript
searchByTitle: publicProcedure
  .input(z.object({ title: z.string() }))
  .query(async ({ input, ctx }) => {
    return searchByTitleProcedure(input, ctx);
  })
```

## Anti-Patterns to Avoid

❌ **Don't**: Put Prisma queries directly in procedures
```typescript
// BAD - Don't do this
const documents = await ctx.prisma.document.findMany({ ... });
```

✅ **Do**: Use services for database operations
```typescript
// GOOD - Do this
const documentService = new DocumentService(ctx.prisma);
const documents = await documentService.getByIds(ids);
```

❌ **Don't**: Make HTTP calls directly in procedures
```typescript
// BAD - Don't do this
const response = await axios.post('http://localhost:8001/summarize', ...);
```

✅ **Do**: Use clients for external API calls
```typescript
// GOOD - Do this
const summaries = await litellmClient.summarizeBatch(documents);
```

## Summary

| Layer | Purpose | Example Files |
|-------|---------|---------------|
| **Routers** | Define API routes, validate input | `routers/search.ts` |
| **Procedures** | Orchestrate business logic | `procedures/summarize.ts` |
| **Services** | Database operations (Prisma) | `services/documents.ts` |
| **Clients** | External API calls (HTTP) | `clients/litellm.ts` |

**Golden Rule**:
- Procedures = orchestration (calls services + clients)
- Services = database only (Prisma)
- Clients = external APIs only (HTTP)

---

**Last Updated**: January 2025
