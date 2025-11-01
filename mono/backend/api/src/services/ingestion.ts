/**
 * Ingestion service - Direct Prisma database operations for ingestion tracking
 */
import { PrismaClient, IngestionRun, IngestionStatus, SourceType } from '@r2d/prisma';
import { logger } from '../utils/logger';

export class IngestionService {
  constructor(private prisma: PrismaClient) {}

  /**
   * Create a new ingestion run
   */
  async createRun(source: SourceType): Promise<IngestionRun> {
    logger.info(`Creating ingestion run for ${source}`);

    return this.prisma.ingestionRun.create({
      data: {
        source,
        status: 'PENDING',
      },
    });
  }

  /**
   * Update ingestion run status
   */
  async updateStatus(id: string, status: IngestionStatus): Promise<IngestionRun> {
    return this.prisma.ingestionRun.update({
      where: { id },
      data: {
        status,
        ...(status === 'COMPLETED' || status === 'FAILED'
          ? { completedAt: new Date() }
          : {}),
      },
    });
  }

  /**
   * Update ingestion run progress
   */
  async updateProgress(
    id: string,
    data: {
      totalFetched?: number;
      totalProcessed?: number;
      totalIndexed?: number;
      errorCount?: number;
    }
  ): Promise<IngestionRun> {
    return this.prisma.ingestionRun.update({
      where: { id },
      data,
    });
  }

  /**
   * Add error to ingestion run
   */
  async addError(id: string, error: string): Promise<IngestionRun> {
    const run = await this.prisma.ingestionRun.findUnique({
      where: { id },
    });

    if (!run) {
      throw new Error(`Ingestion run ${id} not found`);
    }

    return this.prisma.ingestionRun.update({
      where: { id },
      data: {
        errors: [...run.errors, error],
        errorCount: run.errorCount + 1,
      },
    });
  }

  /**
   * Complete ingestion run with final stats
   */
  async completeRun(
    id: string,
    stats: {
      totalFetched: number;
      totalProcessed: number;
      totalIndexed: number;
      errorCount: number;
      errors: string[];
    }
  ): Promise<IngestionRun> {
    logger.info(`Completing ingestion run ${id}`, stats);

    return this.prisma.ingestionRun.update({
      where: { id },
      data: {
        ...stats,
        status: stats.errorCount > 0 ? 'COMPLETED' : 'COMPLETED',
        completedAt: new Date(),
      },
    });
  }

  /**
   * Fail ingestion run
   */
  async failRun(id: string, error: string): Promise<IngestionRun> {
    logger.error(`Ingestion run ${id} failed: ${error}`);

    const run = await this.prisma.ingestionRun.findUnique({
      where: { id },
    });

    if (!run) {
      throw new Error(`Ingestion run ${id} not found`);
    }

    return this.prisma.ingestionRun.update({
      where: { id },
      data: {
        status: 'FAILED',
        errors: [...run.errors, error],
        errorCount: run.errorCount + 1,
        completedAt: new Date(),
      },
    });
  }

  /**
   * Get ingestion run by ID
   */
  async getById(id: string): Promise<IngestionRun | null> {
    return this.prisma.ingestionRun.findUnique({
      where: { id },
    });
  }

  /**
   * Get recent ingestion runs for a source
   */
  async getRecentRuns(source: SourceType, limit: number = 10): Promise<IngestionRun[]> {
    return this.prisma.ingestionRun.findMany({
      where: { source },
      orderBy: {
        startedAt: 'desc',
      },
      take: limit,
    });
  }

  /**
   * Get all ingestion runs
   */
  async getAllRuns(limit: number = 50): Promise<IngestionRun[]> {
    return this.prisma.ingestionRun.findMany({
      orderBy: {
        startedAt: 'desc',
      },
      take: limit,
    });
  }

  /**
   * Get stats for all ingestion runs
   */
  async getStats(): Promise<{
    totalRuns: number;
    successfulRuns: number;
    failedRuns: number;
    totalDocuments: number;
  }> {
    const totalRuns = await this.prisma.ingestionRun.count();
    const successfulRuns = await this.prisma.ingestionRun.count({
      where: { status: 'COMPLETED' },
    });
    const failedRuns = await this.prisma.ingestionRun.count({
      where: { status: 'FAILED' },
    });

    const runs = await this.prisma.ingestionRun.findMany({
      where: { status: 'COMPLETED' },
    });

    const totalDocuments = runs.reduce((sum, run) => sum + run.totalIndexed, 0);

    return {
      totalRuns,
      successfulRuns,
      failedRuns,
      totalDocuments,
    };
  }
}
