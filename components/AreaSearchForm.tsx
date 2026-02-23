'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export function AreaSearchForm(): JSX.Element {
  const [area, setArea] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function submit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const response = await fetch('/api/areas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ area })
    });

    if (!response.ok) {
      setError('Unable to open area page.');
      setIsLoading(false);
      return;
    }

    const data: { normalizedArea: string; correctedArea?: string } = await response.json();
    router.push(`/${data.correctedArea ?? data.normalizedArea}`);
  }

  return (
    <form className="rounded-lg border bg-white p-4 shadow-sm" onSubmit={submit}>
      <label className="mb-2 block text-sm font-medium">Search your area</label>
      <div className="flex gap-2">
        <input
          className="w-full rounded border px-3 py-2"
          value={area}
          onChange={(e) => setArea(e.target.value)}
          placeholder="e.g. kochi"
          required
        />
        <button className="rounded bg-blue-600 px-4 py-2 text-white" disabled={isLoading} type="submit">
          {isLoading ? 'Loading...' : 'Go'}
        </button>
      </div>
      {error ? <p className="mt-2 text-sm text-red-600">{error}</p> : null}
    </form>
  );
}
