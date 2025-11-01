/**
 * Main tRPC router combining all sub-routers
 */
import { router } from '../trpc';
import { searchRouter } from './search';
import { ingestRouter } from './ingest';
import { adminRouter } from './admin';

export const appRouter = router({
  search: searchRouter,
  ingest: ingestRouter,
  admin: adminRouter,
});

export type AppRouter = typeof appRouter;
