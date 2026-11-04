import type { Locale, VoiceProfile } from './types';

const searchKey = (value: string) => value.normalize('NFKC').toLocaleLowerCase().replaceAll('ё', 'е');
export function voicePage(voices: readonly VoiceProfile[], query: string, requestedPage: number, pageSize: number, locale: Locale) {
  const collator = new Intl.Collator(locale, { sensitivity: 'base', numeric: true });
  const term = searchKey(query.trim());
  const filtered = voices.filter(voice => searchKey(voice.name).includes(term)).sort((a,b) => collator.compare(a.name,b.name) || a.id.localeCompare(b.id));
  const size = [6,12,24].includes(pageSize) ? pageSize : 12;
  const pages = Math.max(1, Math.ceil(filtered.length / size));
  const page = Math.max(1, Math.min(Number.isFinite(requestedPage) ? Math.floor(requestedPage) : 1, pages));
  const start = (page - 1) * size;
  return { items: filtered.slice(start,start + size), page, pages, total: filtered.length, from: filtered.length ? start + 1 : 0, to: Math.min(start + size, filtered.length) };
}
