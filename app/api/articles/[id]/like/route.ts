import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import type { ApiErrorResponse, LikeArticleResponse } from '@/lib/types';

export async function POST(
  _request: Request,
  { params }: { params: { id: string } }
): Promise<NextResponse<LikeArticleResponse | ApiErrorResponse>> {
  const articleId = Number(params.id);

  if (Number.isNaN(articleId)) {
    return NextResponse.json({ success: false, error: 'Invalid article id.' }, { status: 400 });
  }

  const updated = await db.article.update({
    where: { id: articleId },
    data: { likes: { increment: 1 } },
    select: { likes: true }
  });

  return NextResponse.json({ success: true, likes: updated.likes });
}
