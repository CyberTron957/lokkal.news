import { NextResponse } from 'next/server';
import { z } from 'zod';
import { db } from '@/lib/db';
import { normalizeAreaName, stringSimilarity } from '@/lib/utils';
import type { AreaSearchResponse, ApiErrorResponse, CreateAreaRequest } from '@/lib/types';

const bodySchema = z.object({
  area: z.string().min(1),
  skipCorrection: z.boolean().optional()
});

export async function POST(request: Request): Promise<NextResponse<AreaSearchResponse | ApiErrorResponse>> {
  const parsed = bodySchema.safeParse((await request.json()) as CreateAreaRequest);

  if (!parsed.success) {
    return NextResponse.json({ success: false, error: 'Invalid request payload.' }, { status: 400 });
  }

  const areaName = normalizeAreaName(parsed.data.area);
  const existing = await db.area.findUnique({ where: { name: areaName } });

  if (existing || parsed.data.skipCorrection) {
    if (!existing) {
      await db.area.create({ data: { name: areaName } });
    }

    return NextResponse.json({ normalizedArea: areaName, created: !existing });
  }

  const allAreas = await db.area.findMany({ select: { name: true } });
  const bestMatch = allAreas
    .map((a) => ({ area: a.name, ratio: stringSimilarity(areaName, a.name) }))
    .sort((a, b) => b.ratio - a.ratio)[0];

  if (bestMatch && bestMatch.ratio >= 0.7) {
    return NextResponse.json({
      normalizedArea: areaName,
      correctedArea: bestMatch.area,
      confidence: 'high',
      created: false
    });
  }

  await db.area.create({ data: { name: areaName } });
  return NextResponse.json({ normalizedArea: areaName, created: true });
}
