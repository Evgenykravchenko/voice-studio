/** Compact project snapshots keep recent links and the explicitly selected recording. */
export function recentTakeIds(ids: readonly string[], selected?: string): string[] {
  const unique = [...new Set(ids)];
  if(selected && !unique.includes(selected))unique.unshift(selected);
  while(unique.length>100)unique.splice(unique[0]===selected?1:0,1);
  return unique;
}
