import test from 'node:test';
import assert from 'node:assert/strict';
import {deliveryEmotions,effectiveDelivery,deliveryLabel} from '../src/delivery.ts';

test('Index offers only the native deliveries connected to the existing request contract',()=>{
  assert.deepEqual(deliveryEmotions('index-tts2'),['calm','excited','angry']);
  for(const value of ['calm','excited','angry'])assert.equal(effectiveDelivery('index-tts2',value),value);
});

test('saved take labels use their own model delivery rather than the currently selected model',()=>{
  assert.equal(deliveryLabel('index-tts2','calm'),'referenceDelivery');
  assert.equal(deliveryLabel('fish-s2-pro','calm'),'calm');
  assert.equal(deliveryLabel('index-tts2','angry'),'angry');
});

test('switching to a model with fewer controls preserves the original scene setting',()=>{
  const scene={text:'Do not remove any words.',emotion:'whisper'};
  assert.equal(effectiveDelivery('index-tts2',scene.emotion),'calm');
  assert.equal(effectiveDelivery('fish-s2-pro',scene.emotion),'whisper');
  assert.equal(scene.emotion,'whisper');assert.equal(scene.text,'Do not remove any words.');
  for(const id of ['fish-s2-pro','qwen3-customvoice','qwen3-voicedesign','moss-voicegenerator','voxcpm2'])assert.equal(deliveryEmotions(id).length,5);
  for(const id of ['kokoro','xtts-v2',undefined]){assert.deepEqual(deliveryEmotions(id),[]);assert.equal(effectiveDelivery(id,'angry'),'calm');}
});
