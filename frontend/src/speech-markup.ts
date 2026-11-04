export interface SpeechEdit { text: string; caret: number }

export function insertSpeechTag(source: string, offset: number, tag: string): SpeechEdit {
  const position = Math.max(0, Math.min(source.length, Number.isFinite(offset) ? Math.trunc(offset) : source.length));
  return { text: source.slice(0, position) + tag + source.slice(position), caret: position + tag.length };
}

export function insertSpeechPause(source: string, offset: number, markup?: string): SpeechEdit {
  let position = Math.max(0, Math.min(source.length, Number.isFinite(offset) ? Math.trunc(offset) : source.length));
  const tags = markup === 'ssml' ? [...source.matchAll(/<!--[\s\S]*?-->|<!\[CDATA\[[\s\S]*?\]\]>|<(?:[^<>"']|"[^"]*"|'[^']*')*>/g)] : [];
  const root = tags[0];
  if (!root || source.slice(0, root.index).trim() || !/^<speak(?:\s|>)/.test(root[0])) {
    return insertSpeechTag(source, position, '\n[pause:0.5]\n');
  }
  const closing = [...tags].reverse().find(tag => /^<\/speak\s*>$/.test(tag[0]));
  position = Math.max(root.index! + root[0].length, Math.min(position, closing?.index ?? source.length));
  // A formatting action must not insert XML inside an attribute or a tag name.
  for (const tag of tags) {
    if (position > tag.index! && position < tag.index! + tag[0].length) {
      position = tag[0].startsWith('</') ? tag.index! : tag.index! + tag[0].length;
      break;
    }
  }
  return insertSpeechTag(source, position, '\n<break time="500ms"/>\n');
}
