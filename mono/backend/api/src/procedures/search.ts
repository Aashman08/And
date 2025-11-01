/**
 * Search procedure - orchestrates hybrid search pipeline
 */
import { Context } from '../context';
import { TRPCError } from '@trpc/server';
import { logger } from '../utils/logger';
import { llamaIndexerClient } from '../clients/llama-indexer';
import { litellmClient } from '../clients/litellm';

interface SearchInput {
  query: string;
  filters?: {
    source?: ('papers' | 'startups')[];
    year_gte?: number;
  };
  limit?: number;
}

export async function searchProcedure(input: SearchInput, ctx: Context) {
  const startTime = Date.now();

  try {
    logger.info(`Search query: "${input.query}"`);

    // Step 1: Hybrid search via llama-indexer service
    // This service handles: BM25 + vector search + blending
    const searchResults = await llamaIndexerClient.hybridSearch({
      query: input.query,
      filters: input.filters,
      top_k: 256, // Get more for reranking
    });

    // Step 2: Rerank using LiteLLM/Cohere
    const reranked = await litellmClient.rerank({
      query: input.query,
      documents: searchResults,
      top_n: input.limit || 20,
    });

    // Step 3: Generate highlights for why_this_result
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

    const duration = Date.now() - startTime;
    logger.info(`Search completed in ${duration}ms, returned ${withHighlights.length} results`);

    return {
      results: withHighlights,
      total: withHighlights.length,
      query: input.query,
      truncated: input.query.length > 512,
    };
  } catch (error) {
    logger.error('Search failed:', error);
    throw new TRPCError({
      code: 'INTERNAL_SERVER_ERROR',
      message: error instanceof Error ? error.message : 'Search failed',
    });
  }
}
