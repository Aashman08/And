/**
 * Main entry point for R&D Discovery API (tRPC)
 */
import express from 'express';
import cors from 'cors';
import { createExpressMiddleware } from '@trpc/server/adapters/express';
import { appRouter } from './routers';
import { createContext } from './context';
import { logger } from './utils/logger';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.API_PORT || 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Health check
app.get('/healthz', (req, res) => {
  res.json({ status: 'ok', service: 'R&D Discovery API', timestamp: new Date().toISOString() });
});

// tRPC middleware
app.use(
  '/trpc',
  createExpressMiddleware({
    router: appRouter,
    createContext,
    onError({ error, type, path }) {
      logger.error(`tRPC Error [${type}] at ${path}:`, error);
    },
  })
);

// Start server
app.listen(PORT, () => {
  logger.info(`🚀 R&D Discovery API running on http://localhost:${PORT}`);
  logger.info(`📡 tRPC endpoint: http://localhost:${PORT}/trpc`);
});

export { appRouter, type AppRouter } from './routers';
