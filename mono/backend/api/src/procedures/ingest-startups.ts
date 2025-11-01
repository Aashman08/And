/**
 * Startups ingestion procedure (via Perplexity API)
 */
import { Context } from '../context';
import { logger } from '../utils/logger';

export async function ingestStartupsProcedure(ctx: Context) {
  logger.info('Starting startup ingestion...');

  // TODO: Implement via llama-indexer service

  const stats = {
    total_fetched: 0,
    total_processed: 0,
    total_indexed: 0,
    error_count: 0,
    errors: [],
  };

  return {
    status: 'completed' as const,
    ...stats,
    message: `Processed ${stats.total_processed} startups`,
  };
}
