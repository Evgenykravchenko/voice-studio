import { test } from 'node:test';
import assert from 'node:assert/strict';
import { audioTime, waveformPeaks } from '../src/audio-utils.ts';

test('waveform includes both channels and preserves later peaks at bucket boundaries', () => {
  const values = waveformPeaks([new Float32Array([0, .25, 0, 0, .5, 0]), new Float32Array([0, 0, -.75, 0, 0, -1])], 3);
  assert.deepEqual(values, [.25, .75, 1]);
});
test('empty or silent audio never produces invented waveform bars', () => {
  assert.deepEqual(waveformPeaks([], 10), []);
  assert.deepEqual(waveformPeaks([new Float32Array(8)], 2), [0, 0]);
});
test('unknown duration and long recordings have safe time labels', () => {
  assert.equal(audioTime(Infinity), '0:00');
  assert.equal(audioTime(NaN), '0:00');
  assert.equal(audioTime(-2), '0:00');
  assert.equal(audioTime(125.99), '2:05');
});
