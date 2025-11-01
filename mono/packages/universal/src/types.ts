// Shared types for R&D Discovery System

export type SourceType = 'papers' | 'startups';

export interface SearchFilters {
  source?: SourceType[];
  year_gte?: number;
}

export interface SearchRequest {
  query: string;
  filters?: SearchFilters;
  limit?: number;
}

export interface SearchMetadata {
  year?: number;
  venue?: string;
  concepts?: string[];
  industry?: string[];
  stage?: string;
  authors?: string[];
  doi?: string;
  website?: string;
}

export interface SearchResult {
  id: string;
  source: SourceType;
  title: string;
  snippet: string;
  score: number;
  why_this_result: string[];
  metadata: SearchMetadata;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

export interface SummarySection {
  problem: string;
  approach: string;
  evidence_or_signals: string;
  result: string;
  limitations: string;
}

export interface SummarizeRequest {
  ids: string[];
}

export interface SummarizeResponse {
  summaries: Record<string, SummarySection>;
}

export interface IngestionProgress {
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  total_fetched: number;
  total_processed: number;
  total_indexed: number;
  error_count: number;
  errors: string[];
}

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'down';
  services?: {
    postgres?: boolean;
    opensearch?: boolean;
    pinecone?: boolean;
  };
}

// Internal retrieval types
export interface RetrievalCandidate {
  doc_id: string;
  score: number;
  source: SourceType;
  title: string;
  snippet: string;
  metadata: SearchMetadata;
}

export interface RankedDocument extends RetrievalCandidate {
  rerank_score?: number;
  highlights: string[];
}
