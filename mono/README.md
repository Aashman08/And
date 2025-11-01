# R&D Discovery System

> **AI-powered platform for discovering relevant research papers and startups across enterprise R&D topics**

## 🎯 Overview

This system combines **BM25 full-text search**, **semantic vector search**, and **LLM-powered reranking** to help R&D teams find the most relevant papers and startups for their technical challenges.

### Key Features

- **Hybrid Search**: Combines OpenSearch (BM25) + Pinecone (vectors) for comprehensive retrieval
- **AI Reranking**: Cohere Rerank v3 for relevance optimization
- **Smart Highlights**: Automatically generates "why this result?" explanations
- **Structured Summaries**: GPT-4o-mini generates 5-section summaries (problem, approach, evidence, result, limitations)
- **Multi-Source Ingestion**: Papers from OpenAlex & arXiv, startups from Perplexity API
- **Type-Safe API**: tRPC for end-to-end TypeScript safety

---

## 🏗️ Architecture

```
Frontend (Next.js 14) → API Gateway (tRPC/TypeScript) → Microservices (Python)
                                                         ├─ LiteLLM (LLM ops)
                                                         └─ Llama-Indexer (Search & Indexing)
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

## 📁 Repository Structure

```
mono/
├── apps/next/              # Next.js frontend
├── backend/
│   ├── api/               # TypeScript/tRPC gateway
│   ├── litellm/           # Python LLM service
│   └── llama-indexer/     # Python search service
├── packages/
│   ├── prisma/            # Database schema
│   └── universal/         # Shared types
├── data/                  # Seed data & eval
├── scripts/               # CLI tools
└── docs/                  # Documentation
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (for services)
- **Node.js 20+** (for local development)
- **Python 3.11+** (for backend)
- **Yarn** (package manager)

### API Keys Required

Create a `.env` file in the root directory:

```bash
# Database
DATABASE_URL=postgresql://r2d:r2d@localhost:5432/r2d

# OpenSearch (if not using Docker defaults)
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200

# Pinecone (required)
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=r2d-chunks

# OpenAI (required)
OPENAI_API_KEY=your-openai-key

# Cohere (required)
COHERE_API_KEY=your-cohere-key

# Perplexity (required for startup ingestion)
PERPLEXITY_API_KEY=your-perplexity-key

# Admin token for protected endpoints
ADMIN_BEARER_TOKEN=your-secure-token
```

### Run with Docker (Recommended)

```bash
# 1. Start all services
make docker-up

# 2. Build search indices
make build-indexes

# 3. Run ingestion
make ingest

# 4. Access the app
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Local Development

```bash
# 1. Install dependencies
make install

# 2. Start databases with Docker
docker-compose up postgres opensearch -d

# 3. Run migrations
cd packages/prisma && npx prisma migrate deploy

# 4. Start dev servers
make dev
# - API: http://localhost:8000
# - Next.js: http://localhost:3000
```

---

## 📖 Usage Guide

### Search API

**POST** `/api/search`

```json
{
  "query": "solid-state batteries for electric vehicles",
  "filters": {
    "source": ["papers"],
    "year_gte": 2020
  },
  "limit": 20
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "doc123",
      "source": "papers",
      "title": "Advanced Solid-State Battery Electrolytes",
      "snippet": "A study on lithium-ion conducting ceramics...",
      "score": 0.95,
      "why_this_result": [
        "Discusses solid-state electrolytes for EVs",
        "Focuses on high energy density materials"
      ],
      "metadata": {
        "year": 2023,
        "venue": "Nature Energy",
        "authors": ["John Doe", "Jane Smith"],
        "doi": "10.1038/example"
      }
    }
  ],
  "total": 15,
  "query": "solid-state batteries for electric vehicles"
}
```

### Summarization API

**POST** `/api/summarize`

```json
{
  "ids": ["doc123", "doc456"]
}
```

**Response:**
```json
{
  "summaries": {
    "doc123": {
      "problem": "Low energy density in current batteries",
      "approach": "Novel ceramic electrolyte materials",
      "evidence_or_signals": "Lab prototype with 40% improvement",
      "result": "Higher energy density and safety",
      "limitations": "High manufacturing costs"
    }
  }
}
```

### CLI Scripts

```bash
# Ingest papers
python scripts/ingest_openalex.py
python scripts/ingest_arxiv.py

# Ingest startups
python scripts/ingest_startups.py

# Evaluate search quality
python scripts/eval_ndcg.py

# Build search indices
python scripts/build_indexes.py
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Backend tests only
make test-api

# Frontend tests only
make test-next
```

### Test Coverage

- **Backend**: 
  - Retrieval pipeline (hybrid search, deduplication)
  - API endpoints (search, summarize)
  - Service mocking with pytest

- **Frontend**:
  - Component rendering
  - User interactions
  - API integration

---

## 📊 Evaluation

The system includes NDCG@10 evaluation on gold-standard queries:

```bash
make eval
```

**Sample Output:**
```
✅ Evaluation complete!
   Average NDCG@10: 0.847
   Queries evaluated: 8/8

Per-query results:
   solid-state battery electrolytes           | NDCG: 0.912
   CRISPR base editing techniques             | NDCG: 0.856
   transformer attention mechanisms           | NDCG: 0.831
   ...
```

---

## 🔧 Configuration

### Embedding Model

Change in `apps/backend/api/app/config.py`:
```python
EMBEDDING_MODEL = "intfloat/e5-base-v2"  # 768 dimensions
```

### Hybrid Search Weights

Adjust in `apps/backend/api/app/services/retriever.py`:
```python
BM25_WEIGHT = 0.6  # Keyword search weight
ANN_WEIGHT = 0.4   # Vector search weight
```

### Reranking Model

Update in `.env`:
```bash
LITELLM_RERANK_MODEL=command-r
```

---

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `postgres` | 5432 | PostgreSQL database |
| `opensearch` | 9200 | BM25 keyword search |
| `api` | 8000 | FastAPI backend |
| `next` | 3000 | Next.js frontend |

View logs:
```bash
make docker-logs
```

Restart services:
```bash
make docker-rebuild
```

---

## 📚 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and service boundaries
- **[Layered Architecture](docs/ARCHITECTURE_LAYERS.md)** - Backend API architecture patterns
- **[Running Locally](docs/Running_the_app_locally.md)** - Complete setup and troubleshooting
- **[Implementation Guide](docs/IMPLEMENTATION_PROMPT.md)** - Guide for completing remaining components
- **[Database Schema](packages/prisma/schema.prisma)** - Prisma schema definition

---

## 🤝 Contributing

1. Create a feature branch
2. Make changes with tests
3. Run linting: `make lint`
4. Run tests: `make test`
5. Submit PR

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **OpenAlex** - Open access to scholarly metadata
- **arXiv** - Preprint repository
- **Pinecone** - Vector database
- **OpenSearch** - BM25 search engine
- **Cohere** - Reranking API
- **OpenAI** - Summarization models
- **Perplexity** - Startup discovery

---

**Built with ❤️ for the research and innovation community**

