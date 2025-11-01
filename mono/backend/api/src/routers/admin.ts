/**
 * Admin router - health checks and system status
 */
import { router, publicProcedure } from '../trpc';
import { litellmClient } from '../clients/litellm';
import { llamaIndexerClient } from '../clients/llama-indexer';

export const adminRouter = router({
  health: publicProcedure.query(async ({ ctx }) => {
    // Check all services
    const [dbHealthy, litellmHealthy, indexerHealthy] = await Promise.all([
      ctx.prisma.$queryRaw`SELECT 1`.then(() => true).catch(() => false),
      litellmClient.healthCheck(),
      llamaIndexerClient.healthCheck(),
    ]);

    const allHealthy = dbHealthy && litellmHealthy && indexerHealthy;

    return {
      status: allHealthy ? 'ok' : 'degraded',
      services: {
        postgres: dbHealthy,
        litellm: litellmHealthy,
        llamaIndexer: indexerHealthy,
      },
      timestamp: new Date().toISOString(),
    };
  }),
});
