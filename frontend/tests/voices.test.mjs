import { test } from 'node:test';
import assert from 'node:assert/strict';
import { assignDefaultVoice, resolveVoiceId } from '../src/voices.ts';

const voices = [{ id: 'first-voice' }, { id: 'second-voice' }];
test('defaults come from available profiles, while explicit selections remain intact', () => {
  assert.equal(resolveVoiceId(undefined, voices), 'first-voice');
  assert.equal(resolveVoiceId('second-voice', voices), 'second-voice');
  assert.equal(resolveVoiceId('unavailable-voice', voices), 'unavailable-voice');
  assert.equal(resolveVoiceId(undefined, []), undefined);
});
test('persist the default once without overwriting drafts or existing voice choices', () => {
  const project = { title: 'Saved project', scenes: [{ id: 'a', text: 'Original text' }, { id: 'b', voiceId: 'second-voice' }] };
  assert.equal(assignDefaultVoice(project, []), project);
  const assigned = assignDefaultVoice(project, voices);
  assert.equal(assigned.scenes[0].voiceId, 'first-voice');
  assert.equal(assigned.scenes[0].text, 'Original text');
  assert.equal(assigned.scenes[1], project.scenes[1]);
  assert.equal(project.scenes[0].voiceId, undefined);
  assert.equal(assignDefaultVoice(assigned, [...voices].reverse()), assigned);
});
