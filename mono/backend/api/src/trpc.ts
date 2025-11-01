/**
 * tRPC initialization and middleware
 */
import { initTRPC, TRPCError } from '@trpc/server';
import { Context } from './context';
import { logger } from './utils/logger';

const t = initTRPC.context<Context>().create();

// Base router and procedure
export const router = t.router;
export const publicProcedure = t.procedure;

// Middleware for timing
const timingMiddleware = t.middleware(async ({ path, type, next }) => {
  const start = Date.now();
  const result = await next();
  const duration = Date.now() - start;
  logger.info(`[${type}] ${path} - ${duration}ms`);
  return result;
});

// Admin-protected procedure
export const adminProcedure = t.procedure
  .use(timingMiddleware)
  .use(async ({ ctx, next }) => {
    const adminToken = process.env.ADMIN_BEARER_TOKEN;

    if (!ctx.token || ctx.token !== adminToken) {
      throw new TRPCError({
        code: 'UNAUTHORIZED',
        message: 'Admin token required',
      });
    }

    return next({ ctx });
  });

// Authenticated procedure (for future use)
export const protectedProcedure = t.procedure
  .use(timingMiddleware)
  .use(async ({ ctx, next }) => {
    if (!ctx.userId) {
      throw new TRPCError({
        code: 'UNAUTHORIZED',
        message: 'Authentication required',
      });
    }

    return next({ ctx });
  });
