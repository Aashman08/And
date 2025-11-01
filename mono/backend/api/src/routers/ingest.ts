/**
 * Ingest router - handles data ingestion from various sources
 */
import { z } from 'zod';
import { router, adminProcedure } from '../trpc';
import { ingestOpenAlexProcedure } from '../procedures/ingest-openalex';
import { ingestArxivProcedure } from '../procedures/ingest-arxiv';
import { ingestStartupsProcedure } from '../procedures/ingest-startups';

export const ingestRouter = router({
  openalex: adminProcedure
    .input(z.object({}).optional())
    .mutation(async ({ ctx }) => {
      return ingestOpenAlexProcedure(ctx);
    }),

  arxiv: adminProcedure
    .input(z.object({}).optional())
    .mutation(async ({ ctx }) => {
      return ingestArxivProcedure(ctx);
    }),

  startups: adminProcedure
    .input(z.object({}).optional())
    .mutation(async ({ ctx }) => {
      return ingestStartupsProcedure(ctx);
    }),
});
