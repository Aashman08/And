/**
 * tRPC context - available to all procedures
 */
import { inferAsyncReturnType } from '@trpc/server';
import { CreateExpressContextOptions } from '@trpc/server/adapters/express';
import { prisma } from '@r2d/prisma';

export const createContext = ({ req, res }: CreateExpressContextOptions) => {
  // Extract auth token if present
  const authHeader = req.headers.authorization;
  const token = authHeader?.startsWith('Bearer ') ? authHeader.substring(7) : null;

  return {
    req,
    res,
    prisma,
    token,
    userId: null, // TODO: Implement auth and set user ID
  };
};

export type Context = inferAsyncReturnType<typeof createContext>;
