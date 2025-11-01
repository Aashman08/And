/**
 * Summarize procedure - generates structured summaries
 *
 * Architecture:
 * - Uses DocumentService (service layer) to fetch from database
 * - Uses litellmClient (client layer) to call external LiteLLM service
 * - Orchestrates the business logic
 */
import { Context } from '../context';
import { TRPCError } from '@trpc/server';
import { logger } from '../utils/logger';
import { litellmClient } from '../clients/litellm';
import { DocumentService } from '../services';

interface SummarizeInput {
  ids: string[];
}

export async function summarizeProcedure(input: SummarizeInput, ctx: Context) {
  try {
    logger.info(`Summarizing ${input.ids.length} documents`);

    // Use DocumentService to fetch documents from database
    const documentService = new DocumentService(ctx.prisma);
    const documents = await documentService.getByIds(input.ids);

    if (documents.length === 0) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'No documents found with the provided IDs',
      });
    }

    // Call external LiteLLM service for summarization
    const summaries = await litellmClient.summarizeBatch(
      documents.map((doc) => ({
        id: doc.id,
        title: doc.title,
        content: doc.description,
        source: doc.source,
      }))
    );

    logger.info(`Generated ${Object.keys(summaries).length} summaries`);

    return { summaries };
  } catch (error) {
    logger.error('Summarization failed:', error);

    if (error instanceof TRPCError) {
      throw error;
    }

    throw new TRPCError({
      code: 'INTERNAL_SERVER_ERROR',
      message: error instanceof Error ? error.message : 'Summarization failed',
    });
  }
}
