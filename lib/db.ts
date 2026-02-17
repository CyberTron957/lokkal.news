import { PrismaClient } from '@prisma/client';
import { PrismaNeon } from '@prisma/adapter-neon';
import { Pool } from '@neondatabase/serverless';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const db =
  globalForPrisma.prisma ??
  (() => {
    const connectionString = process.env.DATABASE_URL;

    if (!connectionString) {
      throw new Error('DATABASE_URL is not set.');
    }

    const pool = new Pool({ connectionString });
    const adapter = new PrismaNeon(pool);

    return new PrismaClient({ adapter });
  })();

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = db;
}
