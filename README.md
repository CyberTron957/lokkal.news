# Lokkal News (Next.js + TypeScript)

This repository has been migrated to a Next.js 14 App Router architecture with strict TypeScript, Prisma, and Neon Postgres.

## Stack
- Next.js 14+
- TypeScript (`strict: true`)
- Prisma + `@prisma/adapter-neon`
- Neon Serverless Postgres
- Tailwind CSS

## Setup
1. Copy env vars:
   ```bash
   cp .env.example .env.local
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run migrations and generate Prisma client:
   ```bash
   npx prisma migrate dev
   ```
4. Start dev server:
   ```bash
   npm run dev
   ```

## API routes
- `POST /api/areas` create/search area with typo correction logic.
- `GET /api/areas/search?term=` autocomplete area names.
- `POST /api/posts` create a community post.
- `POST /api/news/generate` generate article(s) from new posts in an area.
- `POST /api/articles/:id/like` increment article likes.
- `GET /api/trending` fetch trending pages/articles.
