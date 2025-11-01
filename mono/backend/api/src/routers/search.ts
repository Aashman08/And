/**
 * Search router - handles search and summarization
 */
import { z } from 'zod';
import { router, publicProcedure } from '../trpc';
import { searchProcedure } from '../procedures/search';
import { summarizeProcedure } from '../procedures/summarize';

const searchFiltersSchema = z.object({
  source: z.array(z.enum(['papers', 'startups'])).optional(),
  year_gte: z.number().int().min(1900).max(2100).optional(),
});

const searchRequestSchema = z.object({
  query: z.string().min(1).max(512),
  filters: searchFiltersSchema.optional(),
  limit: z.number().int().min(1).max(100).default(20),
});

const summarizeRequestSchema = z.object({
  ids: z.array(z.string()).min(1).max(10),
});

export const searchRouter = router({
  search: publicProcedure
    .input(searchRequestSchema)
    .mutation(async ({ input, ctx }) => {
      return searchProcedure(input, ctx);
    }),

  summarize: publicProcedure
    .input(summarizeRequestSchema)
    .mutation(async ({ input, ctx }) => {
      return summarizeProcedure(input, ctx);
    }),
});
