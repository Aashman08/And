/**
 * Document service - Direct Prisma database operations for documents
 */
import { PrismaClient, Document, SourceType } from '@r2d/prisma';
import { logger } from '../utils/logger';

export class DocumentService {
  constructor(private prisma: PrismaClient) {}

  /**
   * Get document by ID
   */
  async getById(id: string): Promise<Document | null> {
    return this.prisma.document.findUnique({
      where: { id },
      include: {
        chunks: true,
      },
    });
  }

  /**
   * Get multiple documents by IDs
   */
  async getByIds(ids: string[]): Promise<Document[]> {
    return this.prisma.document.findMany({
      where: {
        id: { in: ids },
      },
      include: {
        chunks: true,
      },
    });
  }

  /**
   * Find document by external ID (DOI, arXiv ID, URL hash)
   */
  async findByExternalId(externalId: string): Promise<Document | null> {
    return this.prisma.document.findUnique({
      where: { externalId },
    });
  }

  /**
   * Create a new document
   */
  async create(data: {
    source: SourceType;
    externalId: string;
    title: string;
    description: string;
    year?: number;
    language?: string;
    doi?: string;
    authors?: string[];
    venue?: string;
    concepts?: string[];
    website?: string;
    oneLiner?: string;
    stage?: string;
    industry?: string[];
    country?: string;
  }): Promise<Document> {
    logger.info(`Creating document: ${data.title}`);

    return this.prisma.document.create({
      data,
    });
  }

  /**
   * Create multiple documents
   */
  async createMany(
    documents: Array<{
      source: SourceType;
      externalId: string;
      title: string;
      description: string;
      year?: number;
      language?: string;
      doi?: string;
      authors?: string[];
      venue?: string;
      concepts?: string[];
      website?: string;
      oneLiner?: string;
      stage?: string;
      industry?: string[];
      country?: string;
    }>
  ): Promise<number> {
    const result = await this.prisma.document.createMany({
      data: documents,
      skipDuplicates: true,
    });

    logger.info(`Created ${result.count} documents`);
    return result.count;
  }

  /**
   * Update document
   */
  async update(
    id: string,
    data: Partial<{
      title: string;
      description: string;
      year: number;
      authors: string[];
      venue: string;
      concepts: string[];
      industry: string[];
      stage: string;
    }>
  ): Promise<Document> {
    return this.prisma.document.update({
      where: { id },
      data,
    });
  }

  /**
   * Delete document
   */
  async delete(id: string): Promise<Document> {
    return this.prisma.document.delete({
      where: { id },
    });
  }

  /**
   * Search documents by filters
   */
  async search(params: {
    source?: SourceType[];
    yearGte?: number;
    limit?: number;
    offset?: number;
  }): Promise<Document[]> {
    const { source, yearGte, limit = 100, offset = 0 } = params;

    return this.prisma.document.findMany({
      where: {
        ...(source && { source: { in: source } }),
        ...(yearGte && { year: { gte: yearGte } }),
      },
      take: limit,
      skip: offset,
      orderBy: {
        year: 'desc',
      },
    });
  }

  /**
   * Count documents by source
   */
  async countBySource(source: SourceType): Promise<number> {
    return this.prisma.document.count({
      where: { source },
    });
  }

  /**
   * Get all documents for a source (for export/indexing)
   */
  async getAllBySource(source: SourceType): Promise<Document[]> {
    return this.prisma.document.findMany({
      where: { source },
      include: {
        chunks: true,
      },
    });
  }
}
