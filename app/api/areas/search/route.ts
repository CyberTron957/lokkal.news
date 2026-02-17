import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { normalizeAreaName } from '@/lib/utils';

export async function GET(request: Request): Promise<NextResponse<string[]>> {
  const { searchParams } = new URL(request.url);
  const term = normalizeAreaName(searchParams.get('term'));

  if (!term) return NextResponse.json([]);

  const results = await db.area.findMany({
    where: { name: { contains: term } },
    select: { name: true },
    take: 10
  });

  return NextResponse.json(results.map((r) => r.name));
}
