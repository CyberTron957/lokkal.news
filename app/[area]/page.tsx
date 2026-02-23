import { notFound } from 'next/navigation';
import Link from 'next/link';
import { db } from '@/lib/db';
import { normalizeAreaName } from '@/lib/utils';

export default async function AreaPage({ params }: { params: { area: string } }): Promise<JSX.Element> {
  const normalized = normalizeAreaName(params.area);
  const area = await db.area.findUnique({ where: { name: normalized } });

  if (!area) notFound();

  const [articles, posts] = await Promise.all([
    db.article.findMany({ where: { areaId: area.id }, orderBy: { createdAt: 'desc' } }),
    db.post.findMany({ where: { areaId: area.id }, orderBy: { datePosted: 'desc' }, take: 20 })
  ]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold capitalize">{area.name}</h1>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Latest news</h2>
        <div className="space-y-3">
          {articles.map((article) => (
            <Link className="block rounded border bg-white p-4" href={`/${area.name}/${article.slug}`} key={article.id}>
              <h3 className="font-semibold">{article.title}</h3>
              <p className="line-clamp-2 text-sm text-slate-600">{article.content}</p>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Community posts</h2>
        <div className="space-y-3">
          {posts.map((post) => (
            <article className="rounded border bg-white p-3" key={post.id}>
              <p>{post.content}</p>
              {post.reporterName ? <p className="mt-1 text-xs text-slate-500">By {post.reporterName}</p> : null}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
