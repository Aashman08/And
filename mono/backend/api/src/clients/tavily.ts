/**
 * Tavily API Client
 * 
 * Handles communication with the Tavily web search service
 */
import axios from 'axios';
import { logger } from '../utils/logger';

const TAVILY_SERVICE_URL = process.env.TAVILY_SERVICE_URL || 'http://localhost:8003';

interface TavilySearchParams {
  query: string;
  max_results?: number;
  search_depth?: 'basic' | 'advanced';
  include_domains?: string[];
  exclude_domains?: string[];
}

export interface TavilyResult {
  title: string;
  url: string;
  content: string;
  snippet: string;
  score: number;
  published_date?: string;
}

class TavilyClient {
  private baseURL: string;

  constructor() {
    this.baseURL = TAVILY_SERVICE_URL;
    logger.info(`Tavily client initialized: ${this.baseURL}`);
  }

  /**
   * Search for startups and companies using Tavily web search
   */
  async search(params: TavilySearchParams): Promise<TavilyResult[]> {
    try {
      logger.info(`Tavily search: "${params.query}"`);

      const response = await axios.post<{ results: TavilyResult[]; total: number }>(
        `${this.baseURL}/search`,
        {
          query: params.query,
          max_results: params.max_results || 10,
          search_depth: params.search_depth || 'basic',
          include_domains: params.include_domains,
          exclude_domains: params.exclude_domains,
        },
        {
          timeout: 30000, // 30 second timeout
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      logger.info(`Tavily returned ${response.data.results.length} results`);
      return response.data.results;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        logger.error(`Tavily API error: ${error.message}`);
        if (error.response) {
          logger.error(`Response status: ${error.response.status}`);
        }
      } else {
        logger.error('Tavily search failed:', error);
      }
      // Return empty array on error instead of throwing
      // This way search can continue with just papers
      return [];
    }
  }

  /**
   * Extract content from URLs
   */
  async extractContent(urls: string[]): Promise<Record<string, string>> {
    try {
      logger.info(`Extracting content from ${urls.length} URLs`);

      const response = await axios.post<{ content: Record<string, string> }>(
        `${this.baseURL}/extract`,
        { urls },
        {
          timeout: 30000,
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      return response.data.content;
    } catch (error) {
      logger.error('Tavily extract failed:', error);
      return {};
    }
  }

  /**
   * Health check
   */
  async health(): Promise<boolean> {
    try {
      const response = await axios.get(`${this.baseURL}/health`, {
        timeout: 5000,
      });
      return response.data.status === 'ok';
    } catch (error) {
      logger.error('Tavily health check failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const tavilyClient = new TavilyClient();

