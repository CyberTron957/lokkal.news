import { notFound } from 'next/navigation';
import { db } from '@/lib/db';
import { normalizeAreaName } from '@/lib/utils';

export default async function ArticlePage({ params }: { params: { area: string; articleSlug: string } }): Promise<JSX.Element> {
  const normalized = normalizeAreaName(params.area);

  const area = await db.area.findUnique({ where: { name: normalized } });
  if (!area) notFound();

  const article = await db.article.findFirst({
    where: { areaId: area.id, slug: params.articleSlug },
    include: { questions: true }
  });

  if (!article) notFound();

  return (
    <article className="mx-auto max-w-3xl space-y-4 rounded border bg-white p-6">
      <p className="text-sm uppercase text-slate-500">{article.category}</p>
      <h1 className="text-3xl font-bold">{article.title}</h1>
      {article.reporterName ? <p className="text-sm text-slate-500">By {article.reporterName}</p> : null}
      <p className="whitespace-pre-wrap leading-relaxed">{article.content}</p>
      {article.questions.length ? (
        <section className="pt-4">
          <h2 className="mb-2 font-semibold">Related questions</h2>
          <ul className="list-disc pl-5 text-sm text-slate-700">
            {article.questions.map((q) => (
              <li key={q.id}>{q.question}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </article>
  );
}
