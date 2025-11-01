/**
 * Llama-Indexer service client - handles document indexing and retrieval
 */
import axios, { AxiosInstance } from 'axios';
import { logger } from '../utils/logger';

const LLAMA_INDEXER_BASE_URL = process.env.LLAMA_INDEXER_URL || 'http://localhost:8002';

class LlamaIndexerClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: LLAMA_INDEXER_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Hybrid search combining BM25 and vector search
   */
  async hybridSearch(params: {
    query: string;
    filters?: any;
    top_k: number;
  }): Promise<any[]> {
    try {
      const response = await this.client.post('/search/hybrid', params);
      return response.data.results;
    } catch (error) {
      logger.error('Llama-indexer hybrid search failed:', error);
      throw new Error('Search service unavailable');
    }
  }

  /**
   * Generate highlight sentences for why_this_result
   */
  async generateHighlights(params: {
    query: string;
    text: string;
  }): Promise<string[]> {
    try {
      const response = await this.client.post('/highlights', params);
      return response.data.highlights;
    } catch (error) {
      logger.error('Highlight generation failed:', error);
      // Fallback: return first sentence
      const sentences = params.text.split('. ').slice(0, 3);
      return sentences;
    }
  }

  /**
   * Index documents (papers or startups)
   */
  async indexDocuments(params: {
    documents: any[];
    source: 'papers' | 'startups';
  }): Promise<{ indexed: number; errors: number }> {
    try {
      const response = await this.client.post('/index', params);
      return response.data;
    } catch (error) {
      logger.error('Document indexing failed:', error);
      throw new Error('Indexing service unavailable');
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.data.status === 'ok';
    } catch {
      return false;
    }
  }
}

export const llamaIndexerClient = new LlamaIndexerClient();
