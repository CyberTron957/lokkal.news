import Link from 'next/link';
import { db } from '@/lib/db';
import { AreaSearchForm } from '@/components/AreaSearchForm';

export default async function HomePage(): Promise<JSX.Element> {
  const trendingPages = await db.area.findMany({
    take: 8,
    orderBy: { urlModels: { _count: 'desc' } },
    include: { _count: { select: { urlModels: true } } }
  });

  const trendingArticles = await db.article.findMany({
    take: 6,
    orderBy: [{ createdAt: 'desc' }, { likes: 'desc' }],
    include: { area: true }
  });

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h1 className="text-3xl font-bold">Lokkal News</h1>
        <p className="text-slate-600">Hyperlocal stories, by the people who live there.</p>
        <AreaSearchForm />
      </section>

      <section>
        <h2 className="mb-3 text-xl font-semibold">Trending areas</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {trendingPages.map((area) => (
            <Link className="rounded border bg-white p-3" href={`/${area.name}`} key={area.id}>
              <p className="font-medium capitalize">{area.name}</p>
              <p className="text-sm text-slate-500">{area._count.urlModels} visits</p>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-xl font-semibold">Trending articles</h2>
        <div className="space-y-3">
          {trendingArticles.map((article) => (
            <Link
              className="block rounded border bg-white p-4"
              href={`/${article.area?.name ?? 'unknown'}/${article.slug}`}
              key={article.id}
            >
              <p className="text-sm uppercase text-slate-500">{article.category}</p>
              <h3 className="font-semibold">{article.title}</h3>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
