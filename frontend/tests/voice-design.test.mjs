import test from 'node:test';
import assert from 'node:assert/strict';
import {sparkVoice,sparkDescription,sparkLevels} from '../src/voice-design.ts';

test('all native controlled voices survive project description serialization',()=>{
  for(const gender of ['male','female'])for(const pitch of sparkLevels)for(const speed of sparkLevels){
    const voice={gender,pitch,speed};assert.deepEqual(sparkVoice(sparkDescription(voice)),voice);
  }
});
test('a description from another model offers explicit defaults without modifying the draft',()=>{
  const source='A warm natural voice';assert.deepEqual(sparkVoice(source),{gender:'male',pitch:'moderate',speed:'moderate'});assert.equal(source,'A warm natural voice');
});
