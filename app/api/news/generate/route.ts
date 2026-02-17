import { NextResponse } from 'next/server';
import { z } from 'zod';
import { db } from '@/lib/db';
import { normalizeAreaName, slugWithHash } from '@/lib/utils';
import type { ApiErrorResponse, GenerateNewsRequest } from '@/lib/types';

const schema = z.object({ area: z.string().min(1) });

interface GeneratedArticle {
  title: string;
  content: string;
  category: string;
  reporterName?: string;
}

function buildArticlesFromPosts(posts: Array<{ content: string; reporterName: string | null }>): GeneratedArticle[] {
  if (!posts.length) return [];

  const digest = posts.slice(0, 5).map((p) => p.content).join(' ');
  const reporterName = posts.find((p) => p.reporterName)?.reporterName ?? undefined;

  return [
    {
      title: 'Community update',
      content: digest,
      category: 'news',
      reporterName
    }
  ];
}

export async function POST(request: Request): Promise<NextResponse<{ success: true; created: number } | ApiErrorResponse>> {
  const payload = schema.safeParse((await request.json()) as GenerateNewsRequest);

  if (!payload.success) {
    return NextResponse.json({ success: false, error: 'Area is required.' }, { status: 400 });
  }

  const normalizedArea = normalizeAreaName(payload.data.area);
  const area = await db.area.findUnique({ where: { name: normalizedArea } });

  if (!area) {
    return NextResponse.json({ success: false, error: `Area '${normalizedArea}' not found.` }, { status: 404 });
  }

  const posts = await db.post.findMany({
    where: {
      areaId: area.id,
      ...(area.lastGeneratedAt ? { datePosted: { gt: area.lastGeneratedAt } } : {})
    },
    select: { content: true, reporterName: true },
    orderBy: { datePosted: 'desc' }
  });

  const generated = buildArticlesFromPosts(posts);

  for (const article of generated) {
    await db.article.create({
      data: {
        areaId: area.id,
        title: article.title,
        content: article.content,
        category: article.category,
        reporterName: article.reporterName,
        slug: slugWithHash(article.title)
      }
    });
  }

  await db.area.update({
    where: { id: area.id },
    data: { lastGeneratedAt: new Date() }
  });

  return NextResponse.json({ success: true, created: generated.length });
}
