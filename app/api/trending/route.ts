import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import type { TrendingResponse } from '@/lib/types';

export async function GET(): Promise<NextResponse<TrendingResponse>> {
  const [areas, articles] = await Promise.all([
    db.area.findMany({
      take: 8,
      include: { _count: { select: { urlModels: true } } },
      orderBy: { urlModels: { _count: 'desc' } }
    }),
    db.article.findMany({
      take: 6,
      include: { area: true },
      orderBy: [{ createdAt: 'desc' }, { likes: 'desc' }]
    })
  ]);

  return NextResponse.json({
    trendingPages: areas.map((area) => ({ path: area.name, visits: area._count.urlModels, name: area.name })),
    trendingArticles: articles
  });
}
