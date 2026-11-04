import test from 'node:test';
import assert from 'node:assert/strict';
import { insertSpeechTag, insertSpeechPause } from '../src/speech-markup.ts';

test('formatting tags are inserted without replacing speech or negations', () => {
  const source = 'Я не согласен. Всё ещё обсуждаем.';
  const edit = insertSpeechTag(source, 2, '[calm] ');
  assert.equal(edit.text, 'Я [calm] не согласен. Всё ещё обсуждаем.');
  assert.equal(edit.text.replace('[calm] ', ''), source);
  assert.equal(edit.caret, 9);
});

test('ordinary text keeps the shared PCM pause syntax, including plain Silero input', () => {
  const source = 'Please keep every word in this recording.';
  for (const markup of [undefined, 'plain', 'ssml', 'dia']) {
    const edit = insertSpeechPause(source, 22, markup);
    assert.equal(edit.text.replace('\n[pause:0.5]\n', ''), source);
    assert.equal(edit.text, 'Please keep every word\n[pause:0.5]\n in this recording.');
  }
});

test('SSML pauses stay in the speak body and outside tags, attributes and comments', () => {
  const samples = [
    ['<speak>Текст.</speak>', 99, '<speak>Текст.'],
    ['<speak>Текст.</speak>', 0, '<speak>'],
    ['<speak><prosody rate="slow">Не теряйте слова.</prosody></speak>', 25, '<speak><prosody rate="slow">'],
    ['<speak><prosody rate="slow">Текст.</prosody></speak>', 37, '<speak><prosody rate="slow">Текст.'],
    ['<speak><!-- keep > note -->Текст.</speak><!-- footer -->', 15, '<speak><!-- keep > note -->'],
    ['<speak>Текст.</speak><!-- footer -->', 99, '<speak>Текст.'],
  ];
  for (const [source, position, prefix] of samples) {
    const edit = insertSpeechPause(source, position, 'ssml');
    assert.equal(edit.text.replace('\n<break time="500ms"/>\n', ''), source);
    assert.equal(edit.text, prefix + '\n<break time="500ms"/>\n' + source.slice(prefix.length));
    assert.equal(edit.caret, prefix.length + '\n<break time="500ms"/>\n'.length);
  }
});
