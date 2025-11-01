/**
 * Chunk service - Direct Prisma database operations for chunks
 */
import { PrismaClient, Chunk } from '@r2d/prisma';
import { logger } from '../utils/logger';

export class ChunkService {
  constructor(private prisma: PrismaClient) {}

  /**
   * Get chunk by ID
   */
  async getById(id: string): Promise<Chunk | null> {
    return this.prisma.chunk.findUnique({
      where: { id },
      include: {
        document: true,
      },
    });
  }

  /**
   * Get all chunks for a document
   */
  async getByDocumentId(documentId: string): Promise<Chunk[]> {
    return this.prisma.chunk.findMany({
      where: { documentId },
      orderBy: {
        chunkIndex: 'asc',
      },
    });
  }

  /**
   * Create a new chunk
   */
  async create(data: {
    documentId: string;
    chunkIndex: number;
    text: string;
    section?: string;
    vectorId?: string;
  }): Promise<Chunk> {
    return this.prisma.chunk.create({
      data,
    });
  }

  /**
   * Create multiple chunks for a document
   */
  async createMany(
    chunks: Array<{
      documentId: string;
      chunkIndex: number;
      text: string;
      section?: string;
      vectorId?: string;
    }>
  ): Promise<number> {
    const result = await this.prisma.chunk.createMany({
      data: chunks,
    });

    logger.info(`Created ${result.count} chunks`);
    return result.count;
  }

  /**
   * Update chunk with vector ID (after Pinecone upload)
   */
  async updateVectorId(id: string, vectorId: string): Promise<Chunk> {
    return this.prisma.chunk.update({
      where: { id },
      data: { vectorId },
    });
  }

  /**
   * Get chunk by vector ID
   */
  async getByVectorId(vectorId: string): Promise<Chunk | null> {
    return this.prisma.chunk.findUnique({
      where: { vectorId },
      include: {
        document: true,
      },
    });
  }

  /**
   * Delete all chunks for a document
   */
  async deleteByDocumentId(documentId: string): Promise<number> {
    const result = await this.prisma.chunk.deleteMany({
      where: { documentId },
    });

    return result.count;
  }

  /**
   * Count total chunks in database
   */
  async count(): Promise<number> {
    return this.prisma.chunk.count();
  }

  /**
   * Get chunks without vector IDs (not yet uploaded to Pinecone)
   */
  async getChunksWithoutVectors(limit: number = 100): Promise<Chunk[]> {
    return this.prisma.chunk.findMany({
      where: {
        vectorId: null,
      },
      take: limit,
      include: {
        document: true,
      },
    });
  }
}
