import test from 'node:test';
import assert from 'node:assert/strict';
import {recentTakeIds} from '../src/take-links.ts';
import {mergeServerTakes} from '../src/project-sync.ts';

test('recent links preserve an explicit old take without mutating either input list',()=>{
 const ids=Array.from({length:130},(_,i)=>String(i)),before=[...ids];const result=recentTakeIds(ids,'0');assert.equal(result.length,100);assert.equal(result[0],'0');assert.equal(result.at(-1),'129');assert.deepEqual(ids,before);assert.equal(new Set(result).size,100);
 assert.deepEqual(recentTakeIds(['a','b','a'],'z'),['z','a','b']);
});
test('merging concurrent server takes retains a manual choice outside the recent window',()=>{
 const ids=Array.from({length:130},(_,i)=>String(i)),scene={id:'s',text:'Do not change any words.',takeIds:ids.slice(0,100),selectedTakeId:'99'};const base={title:'Project',scenes:[scene]},local={...base,scenes:[{...scene,selectedTakeId:'0'}]},remote={...base,scenes:[{...scene,takeIds:ids.slice(-100),selectedTakeId:'129'}]};
 const merged=mergeServerTakes(local,base,remote).scenes[0];assert.equal(merged.selectedTakeId,'0');assert.ok(merged.takeIds.includes('0'));assert.ok(merged.takeIds.includes('129'));assert.equal(merged.takeIds.length,100);assert.equal(merged.text,scene.text);
});
