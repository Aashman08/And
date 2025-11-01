.PHONY: help install dev build test lint clean ingest eval docker-up docker-down docker-logs

# Default target
help:
	@echo "R&D Discovery System - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Development:"
	@echo "  make install      Install all dependencies"
	@echo "  make dev          Run development servers"
	@echo "  make build        Build all services"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-api     Run backend tests only"
	@echo "  make test-next    Run frontend tests only"
	@echo "  make lint         Run linters"
	@echo ""
	@echo "Data:"
	@echo "  make build-indexes  Create search indices"
	@echo "  make ingest        Run all ingestion scripts"
	@echo "  make ingest-papers Run paper ingestion (OpenAlex + arXiv)"
	@echo "  make ingest-startups Run startup ingestion"
	@echo "  make eval          Evaluate search quality (NDCG)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    Start all services with Docker Compose"
	@echo "  make docker-down  Stop all services"
	@echo "  make docker-logs  View service logs"
	@echo "  make docker-rebuild  Rebuild and restart services"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        Remove build artifacts and caches"
	@echo ""

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	yarn install
	cd apps/backend/api && pip install -r requirements.txt

# Development servers
dev:
	@echo "🚀 Starting development servers..."
	@echo "Note: Run 'make docker-up' first to start databases"
	yarn dev

# Build all services
build:
	@echo "🏗️  Building all services..."
	yarn build

# Run all tests
test:
	@echo "🧪 Running all tests..."
	@$(MAKE) test-api
	@$(MAKE) test-next

# Run backend tests
test-api:
	@echo "🧪 Running backend tests..."
	cd apps/backend/api && pytest

# Run frontend tests
test-next:
	@echo "🧪 Running frontend tests..."
	cd apps/next && yarn test:ci

# Linting
lint:
	@echo "🔍 Running linters..."
	cd apps/backend/api && black . && isort .
	cd apps/next && yarn lint

# Build search indexes
build-indexes:
	@echo "📦 Building search indexes..."
	python scripts/build_indexes.py

# Run all ingestion
ingest:
	@echo "📥 Running all ingestion scripts..."
	@$(MAKE) ingest-papers
	@$(MAKE) ingest-startups

# Run paper ingestion
ingest-papers:
	@echo "📥 Ingesting papers..."
	python scripts/ingest_openalex.py
	python scripts/ingest_arxiv.py

# Run startup ingestion
ingest-startups:
	@echo "📥 Ingesting startups..."
	python scripts/ingest_startups.py

# Evaluate search quality
eval:
	@echo "📊 Evaluating search quality..."
	python scripts/eval_ndcg.py

# Docker commands
docker-up:
	@echo "🐳 Starting services with Docker Compose..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "   API: http://localhost:8000"
	@echo "   Next.js: http://localhost:3000"
	@echo "   OpenSearch: http://localhost:9200"
	@echo "   PostgreSQL: localhost:5432"

docker-down:
	@echo "🐳 Stopping services..."
	docker-compose down

docker-logs:
	@echo "📋 Viewing service logs..."
	docker-compose logs -f

docker-rebuild:
	@echo "🐳 Rebuilding and restarting services..."
	docker-compose up -d --build

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

