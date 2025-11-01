/**
 * Search procedure - orchestrates parallel search across Tavily (startups) and Database (papers)
 */
import { Context } from '../context';
import { TRPCError } from '@trpc/server';
import { logger } from '../utils/logger';
import { llamaIndexerClient } from '../clients/llama-indexer';
import { litellmClient } from '../clients/litellm';
import { tavilyClient, TavilyResult } from '../clients/tavily';

interface SearchInput {
  query: string;
  filters?: {
    source?: ('papers' | 'startups')[];
    year_gte?: number;
  };
  limit?: number;
}

interface SearchResult {
  id: string;
  title: string;
  snippet: string;
  source: 'papers' | 'startups';
  url?: string;
  why_this_result?: string[];
  [key: string]: any;
}

export async function searchProcedure(input: SearchInput, ctx: Context) {
  const startTime = Date.now();

  try {
    logger.info(`Search query: "${input.query}"`);

    // Run BOTH searches in parallel
    const [tavilyResults, databaseResults] = await Promise.all([
      // Call 1: Tavily for web search (startups/companies)
      tavilyClient.search({
        query: input.query,
        max_results: 10,
        search_depth: 'basic',
      }),

      // Call 2: Database search for papers (existing flow)
      (async () => {
        // Step 1: Hybrid search via llama-indexer
        const searchResults = await llamaIndexerClient.hybridSearch({
          query: input.query,
          filters: input.filters,
          top_k: 256, // Get more for reranking
        });

        // Step 2: Rerank using Cohere
        const reranked = await litellmClient.rerank({
          query: input.query,
          documents: searchResults,
          top_n: 20, // Top 20 papers
        });

        // Step 3: Generate highlights
        const withHighlights = await Promise.all(
          reranked.map(async (doc) => {
            const highlights = await llamaIndexerClient.generateHighlights({
              query: input.query,
              text: doc.snippet,
            });

            return {
              ...doc,
              why_this_result: highlights,
            };
          })
        );

        return withHighlights;
      })(),
    ]);

    // Format Tavily results as startup objects
    const startups: SearchResult[] = tavilyResults.map((result, index) => ({
      id: `tavily-${index}`,
      title: result.title,
      snippet: result.snippet || result.content.substring(0, 200),
      source: 'startups' as const,
      url: result.url,
      score: result.score,
      published_date: result.published_date,
      why_this_result: [result.content.substring(0, 150) + '...'], // Brief excerpt
    }));

    const duration = Date.now() - startTime;
    logger.info(
      `Search completed in ${duration}ms: ${startups.length} startups, ${databaseResults.length} papers`
    );

    // Return separate lists
    return {
      startups: startups,           // Top 10 from Tavily
      papers: databaseResults,       // Top 20 from database
      query: input.query,
      total: startups.length + databaseResults.length,
    };
  } catch (error) {
    logger.error('Search failed:', error);
    throw new TRPCError({
      code: 'INTERNAL_SERVER_ERROR',
      message: error instanceof Error ? error.message : 'Search failed',
    });
  }
}
