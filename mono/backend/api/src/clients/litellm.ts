/**
 * LiteLLM service client - handles LLM operations (reranking, summarization)
 */
import axios, { AxiosInstance } from 'axios';
import { logger } from '../utils/logger';

const LITELLM_BASE_URL = process.env.LITELLM_URL || 'http://localhost:8001';

class LiteLLMClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: LITELLM_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Rerank documents using Cohere Rerank API
   */
  async rerank(params: {
    query: string;
    documents: any[];
    top_n: number;
  }): Promise<any[]> {
    try {
      const response = await this.client.post('/rerank', params);
      return response.data.results;
    } catch (error) {
      logger.error('LiteLLM rerank failed:', error);
      // Fallback: return original documents
      return params.documents.slice(0, params.top_n);
    }
  }

  /**
   * Generate structured summaries using OpenAI
   */
  async summarizeBatch(documents: Array<{
    id: string;
    title: string;
    content: string;
    source: string;
  }>): Promise<Record<string, any>> {
    try {
      const response = await this.client.post('/summarize', { documents });
      return response.data.summaries;
    } catch (error) {
      logger.error('LiteLLM summarize failed:', error);
      throw new Error('Summarization service unavailable');
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

export const litellmClient = new LiteLLMClient();
