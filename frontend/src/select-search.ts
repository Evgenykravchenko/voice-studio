export function filterSelectOptions<T extends { value: string; label: string }>(options: T[], query: string): T[] {
  const fold = (text: string) => text.normalize('NFKD').replace(/\p{M}/gu, '').toLocaleLowerCase();
  const terms = fold(query).trim().split(/\s+/).filter(Boolean);
  if (!terms.length) return options;
  const matches = options.filter(option => terms.every(term => fold(`${option.label} ${option.value}`).includes(term)));
  const exact = matches.filter(option => fold(option.value) === terms.join(' '));
  return [...exact, ...matches.filter(option => !exact.includes(option))];
}
