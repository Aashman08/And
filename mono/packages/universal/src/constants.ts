// Shared constants for R&D Discovery System

// Search configuration
export const HYBRID_BM25_WEIGHT = 0.6;
export const HYBRID_ANN_WEIGHT = 0.4;
export const BM25_TOP_K = 200;
export const ANN_TOP_K = 200;
export const RERANK_TOP_K = 256;
export const FINAL_TOP_N = 30;
export const DEFAULT_SEARCH_LIMIT = 20;
export const MAX_QUERY_LENGTH = 512;

// Chunking configuration
export const CHUNK_TARGET_TOKENS = 512;
export const CHUNK_STRIDE_TOKENS = 64;

// Ingestion configuration
export const OPENALEX_TOPICS = [
  'materials science',
  'battery',
  'biotechnology',
  'machine learning',
];
export const ARXIV_CATEGORIES = ['cs.LG', 'cond-mat.mtrl-sci'];
export const INGESTION_YEARS_BACK = 3;
export const WORKS_PER_TOPIC = 200;
export const WORKS_PER_CATEGORY = 200;

// Rate limiting
export const MAX_REQUESTS_PER_SECOND = 5;
export const MAX_CONCURRENT_HTTP = 8;

// Timeouts (milliseconds)
export const UPSTREAM_API_TIMEOUT = 15000;
export const INTERNAL_OP_TIMEOUT = 30000;

// Latency targets (milliseconds)
export const SEARCH_P50_TARGET = 2500;
export const SEARCH_P95_TARGET = 6000;

// OpenSearch indices
export const OPENSEARCH_PAPERS_INDEX = 'papers_bm25';
export const OPENSEARCH_STARTUPS_INDEX = 'startups_bm25';

// Embedding configuration
export const QUERY_PREFIX = 'query: ';
export const PASSAGE_PREFIX = 'passage: ';

// Highlight configuration
export const MAX_HIGHLIGHTS_PER_RESULT = 3;
