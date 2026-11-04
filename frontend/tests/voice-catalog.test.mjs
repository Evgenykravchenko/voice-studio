import {test} from 'node:test';
import assert from 'node:assert/strict';
import {voicePage} from '../src/voice-catalog.ts';
const voices=Array.from({length:25},(_,i)=>({id:`voice-${i+1}`,name:`Voice ${i+1}`}));
test('paginate deterministically without changing source profile order',()=>{
 const source=[...voices].reverse(), original=source.map(v=>v.id);
 const first=voicePage(source,'',1,12,'en'),last=voicePage(source,'',3,12,'en');
 assert.deepEqual(first.items.map(v=>v.name),voices.slice(0,12).map(v=>v.name));
 assert.equal(first.pages,3);assert.equal(first.from,1);assert.equal(first.to,12);
 assert.equal(last.items[0].name,'Voice 25');assert.equal(last.from,25);assert.equal(last.to,25);
 assert.deepEqual(source.map(v=>v.id),original);
});
test('search trims whitespace, ignores case and treats Russian е/ё alike',()=>{
 const records=[{id:'a',name:'Актёр — студия'},{id:'b',name:'Рассказчик'}];
 assert.deepEqual(voicePage(records,' АКТЕР ',1,6,'ru').items.map(v=>v.id),['a']);
 assert.equal(voicePage(records,'неизвестный',1,6,'ru').total,0);
});
test('filtering and deleting the last item clamp the page instead of leaving a blank page',()=>{
 assert.equal(voicePage(voices.slice(0,24),'',3,12,'en').page,2);
 const empty=voicePage([],'',5,6,'en');assert.equal(empty.page,1);assert.equal(empty.from,0);assert.equal(empty.to,0);
 assert.equal(voicePage(voices,'Voice 25',3,12,'en').page,1);
 assert.equal(voicePage(voices,'',-4,12,'en').page,1);
 assert.equal(voicePage(voices,'',NaN,12,'en').page,1);
 assert.equal(voicePage(voices,'',1,0,'en').items.length,12);
});
