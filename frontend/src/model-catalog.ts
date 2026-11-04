import type { CatalogModel, Locale } from './types';

export interface CatalogFilters { query: string; task: string; status: string; language: string; feature: string; integration: string; }
export function canonicalLanguage(code: string): string {
  try { return Intl.getCanonicalLocales(code)[0]?.toLowerCase() ?? code.toLowerCase(); }
  catch { return code.toLowerCase(); }
}
export function modelMatches(model: CatalogModel, query: string, task: string, status: string, language = 'all', feature = 'all', integration = 'all'): boolean {
  const text = `${model.name} ${model.format} ${model.repo} ${typeof model.description === 'object' ? Object.values(model.description).join(' ') : ''}`.toLocaleLowerCase();
  const usable = model.integration === 'ready' ? model.ready : model.installed;
  return text.includes(query.trim().toLocaleLowerCase()) && (task === 'all' || model.task === task)
    && (status === 'all' || (status === 'installed' ? usable : status === 'downloads' ? ['queued', 'downloading', 'verifying', 'preparing'].includes(model.status) : !usable))
    && (language === 'all' || model.languages?.some(code => canonicalLanguage(code) === canonicalLanguage(language)))
    && (feature === 'all' || model.features?.includes(feature))
    && (integration === 'all' || (integration === 'ready' ? model.integration === 'ready' : model.integration !== 'ready'));
}
export function modelBytes(bytes: number | null, locale: Locale): string {
  if (bytes == null) return locale === 'ru' ? 'См. автора' : 'See source';
  const unit = bytes >= 1e9 ? 1e9 : 1e6;
  return `${new Intl.NumberFormat(locale, { maximumFractionDigits: unit === 1e9 ? 2 : 0 }).format(bytes / unit)} ${locale === 'ru' ? unit === 1e9 ? 'ГБ' : 'МБ' : unit === 1e9 ? 'GB' : 'MB'}`;
}
export function modelLanguages(languages: string[], locale: Locale): string {
  if (!languages.length) return locale === 'ru' ? 'Не зависит от языка' : 'Language independent';
  const canonical = languages.map(canonicalLanguage);
  const ordered = [...new Set(['ru','en',...canonical].filter(code => canonical.includes(code)))];
  const names = new Intl.DisplayNames([locale], { type: 'language' });
  const first = ordered.slice(0,2).map(code => names.of(code) ?? code).join(', ');
  return first + (ordered.length > 2 ? ` +${ordered.length - 2}` : '');
}
export function modelLanguageOptions(models: Pick<CatalogModel, 'languages'>[], locale: Locale, current = 'all') {
  const codes = [...new Set([...models.flatMap(model => model.languages), ...(current === 'all' ? [] : [current])].map(canonicalLanguage))].filter(code => code !== 'auto');
  const names = new Intl.DisplayNames([locale], { type: 'language' });
  const collator = new Intl.Collator(locale);
  const priority = (code: string) => code === 'ru' ? 0 : code === 'en' ? 1 : 2;
  const options = codes.map(value => {
    let label = value;
    try { label = names.of(value) ?? value; } catch { /* Keep an older catalog link readable. */ }
    return { value, label: label.charAt(0).toLocaleUpperCase(locale) + label.slice(1) };
  });
  // Some localized names coincide even for distinct languages (e.g. Akan/Twi).
  const counts = new Map<string, number>();
  for (const option of options) counts.set(option.label, (counts.get(option.label) ?? 0) + 1);
  return options.map(option => ({...option,label:counts.get(option.label)! > 1 ? `${option.label} (${option.value})` : option.label}))
    .sort((a, b) => priority(a.value) - priority(b.value) || collator.compare(a.label, b.label));
}
export function catalogFilters(search: string): CatalogFilters {
  const params = new URLSearchParams(search);
  const allowed = (key: string, values: string[]) => { const value = params.get(key) ?? 'all'; return values.includes(value) ? value : 'all'; };
  const language = params.get('language') ?? 'all';
  return { query: (params.get('q') ?? '').slice(0, 200),
    task: allowed('task', ['all','synthesis','transcription','processing','conversion']),
    status: allowed('status', ['all','installed','available','downloads']),
    language: language === 'all' ? 'all' : (language.length <= 35 && /^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$/.test(language)) ? canonicalLanguage(language) : 'all',
    feature: allowed('feature', ['all','cloning','presets','design','dialogue','emotion','streaming','ssml','sound-effects','enhancement','conversion']),
    integration: allowed('integration', ['all','ready','other']) };
}
