import crypto from 'node:crypto';

export const STOP_WORDS = new Set([
  'a','an','and','are','as','at','be','but','by','for','if','in','into','is','it','no','not','of','on','or','such','that','the','their','then','there','these','they','this','to','was','will','with','over','post-oc'
]);

export function normalizeAreaName(name: string | null | undefined): string {
  if (!name) return '';
  return name.toLowerCase().trim().replace(/\s+/g, ' ');
}

export function slugWithHash(input: string, prefix = ''): string {
  const baseSlug = input
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');

  const hash = crypto.createHash('sha256').update(input).digest('hex').slice(0, 12);
  return `${prefix}${baseSlug}-${hash}`;
}

export function stringSimilarity(a: string, b: string): number {
  if (a === b) return 1;
  if (!a.length || !b.length) return 0;

  const longer = a.length > b.length ? a : b;
  const shorter = a.length > b.length ? b : a;

  let matches = 0;
  for (const char of shorter) {
    if (longer.includes(char)) matches += 1;
  }

  return matches / longer.length;
}
