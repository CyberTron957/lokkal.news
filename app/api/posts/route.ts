import { NextResponse } from 'next/server';
import { z } from 'zod';
import { db } from '@/lib/db';
import { normalizeAreaName } from '@/lib/utils';
import type { ApiErrorResponse, CreatePostRequest } from '@/lib/types';

const schema = z.object({
  area: z.string().min(1),
  content: z.string().min(1),
  reporterName: z.string().optional(),
  image: z.string().url().optional()
});

export async function POST(request: Request): Promise<NextResponse<{ success: true; id: number } | ApiErrorResponse>> {
  const payload = schema.safeParse((await request.json()) as CreatePostRequest);

  if (!payload.success) {
    return NextResponse.json({ success: false, error: 'Invalid request.' }, { status: 400 });
  }

  const areaName = normalizeAreaName(payload.data.area);
  const area = await db.area.upsert({
    where: { name: areaName },
    update: {},
    create: { name: areaName }
  });

  const post = await db.post.create({
    data: {
      areaId: area.id,
      content: payload.data.content,
      reporterName: payload.data.reporterName,
      image: payload.data.image
    }
  });

  return NextResponse.json({ success: true, id: post.id });
}
