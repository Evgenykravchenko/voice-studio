import { test } from 'node:test';
import assert from 'node:assert/strict';
import { canTranscribeLanguage, referenceLanguageOptions, MAX_AUDIO_BYTES, recordingError, validateVoiceForm, validateVoiceReview } from '../src/voice-form.ts';

const valid = { name: 'Тестовый голос', file: { name: 'Запись.M4A', size: 1000 }, start: '0', duration: '20' };
test('a valid local recording accepts supported uppercase formats and range boundaries', () => {
  assert.deepEqual(validateVoiceForm(valid), {});
  assert.deepEqual(validateVoiceForm({ ...valid, duration: '5', start: '86400' }), {});
  assert.deepEqual(validateVoiceForm({ ...valid, duration: '30' }), {});
});
test('missing or malformed form values point to individual fields', () => {
  assert.deepEqual(validateVoiceForm({ name: ' ', file: null, start: 'NaN', duration: '31' }), { name: 'voiceNameRequired', file: 'recordingRequired', start: 'invalidClipStart', duration: 'invalidClipDuration' });
  assert.equal(validateVoiceForm({ ...valid, start: '', duration: '' }).start, 'invalidClipStart');
  assert.equal(validateVoiceForm({ ...valid, duration: 'Infinity' }).duration, 'invalidClipDuration');
});
test('unsupported, empty and oversized recordings are rejected before upload', () => {
  assert.equal(recordingError({ name: 'audio.wav.html', size: 100 }), 'audioUnsupported');
  assert.equal(recordingError({ name: 'audio.wav', size: 0 }), 'audioEmpty');
  assert.equal(recordingError({ name: 'audio.wav', size: MAX_AUDIO_BYTES + 1 }), 'audioTooLarge');
});
test('review requires both name and exact reference text', () => {
  assert.deepEqual(validateVoiceReview('Тестовый голос', ''), { transcript: 'transcriptRequired' });
  assert.equal(validateVoiceReview('a'.repeat(81), 'Текст.').name, 'voiceNameTooLong');
  assert.deepEqual(validateVoiceReview('Тестовый голос', 'Не меняй эти слова!'), {});
});

test('a Russian-only recognizer does not silently accept an English reference', () => {
  assert.equal(canTranscribeLanguage('ru',['ru']),true);
  assert.equal(canTranscribeLanguage('auto',['ru']),true);
  assert.equal(canTranscribeLanguage('en',['ru']),false);
  assert.equal(canTranscribeLanguage('en',['ru','en']),true);
  assert.equal(canTranscribeLanguage('ru',[]),false);
});

test('reference languages follow the recognizer while retaining an unsupported draft selection', () => {
  const options = referenceLanguageOptions(['ja','en','yue','ja'], 'ru', 'en', true, 'Automatic');
  assert.deepEqual(options.map(option => option.value), ['ja','en','yue','ru','auto']);
  assert.equal(options[0].label, 'Japanese');
  assert.equal(options[2].label, 'Cantonese');
  assert.equal(canTranscribeLanguage('ru', ['ja','en','yue']), false);
  assert.deepEqual(referenceLanguageOptions(['ru'], 'ja', 'ru', true, 'Автоматически'), [
    {value:'ru',label:'Русский'}, {value:'ja',label:'Японский'}, {value:'auto',label:'Автоматически'},
  ]);
});

test('legacy servers expose only their accepted recording languages without losing a newer draft', () => {
  assert.deepEqual(referenceLanguageOptions(['ru','en','ja'], 'en', 'en', false, 'Automatic').map(option => option.value), ['ru','en','auto']);
  assert.deepEqual(referenceLanguageOptions(['ru','en','ja'], 'ja', 'en', false, 'Automatic').map(option => option.value), ['ru','en','ja','auto']);
  assert.equal(referenceLanguageOptions([], 'invalid_draft', 'ru', true, 'Автоматически')[0].value, 'invalid_draft');
});
