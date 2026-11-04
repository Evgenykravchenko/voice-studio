import {test} from 'node:test';
import assert from 'node:assert/strict';
import {libraryPage,pagedLibraryPage} from '../src/library-page.ts';
const recordings=Array.from({length:27},(_,i)=>({id:String(i),title:i===2?'Актёр':'Record '+i,sourceText:'Exact text '+i,generated:i>2,available:i!==26}));
test('library pages keep playback source indices and put recent generated takes before samples',()=>{const result=libraryPage(recordings,'',1,12,'all');assert.equal(result.total,26);assert.equal(result.pages,3);assert.equal(result.items[0].index,25);assert.equal(recordings[25].id,result.items[0].id);assert.equal(libraryPage(recordings,'',1,12,'samples').items.length,3);});
test('library searches exact source text and normalizes Russian letters',()=>{assert.equal(libraryPage(recordings,'АКТЕР',1,12,'all').items[0].index,2);assert.equal(libraryPage(recordings,'Exact text 11',1,12,'generated').items[0].index,11);assert.equal(libraryPage(recordings,'unknown',10,12,'all').page,1);assert.equal(libraryPage(recordings,'',99,6,'all').page,5);});
test('server pages keep global playback indices and append samples only after generated history',()=>{
 const ids=Array.from({length:12},(_,i)=>String(25-i));const first=pagedLibraryPage(recordings,ids,23,'',1,12,'all');assert.equal(first.total,26);assert.equal(first.pages,3);assert.deepEqual(first.items.map(x=>x.index),ids.map(Number));
 const next=pagedLibraryPage(recordings,Array.from({length:11},(_,i)=>String(13-i)),23,'',2,12,'all');assert.equal(next.items.length,12);assert.equal(next.items.at(-1).generated,false);
 const tail=pagedLibraryPage(recordings,[],23,'',3,12,'all');assert.equal(tail.items.length,2);assert.ok(tail.items.every(x=>!x.generated));assert.equal(new Set([...first.items,...next.items,...tail.items].map(x=>x.index)).size,26);
 const noCachedRows=pagedLibraryPage(recordings,Array.from({length:12},(_,i)=>'not-loaded-'+i),130,'',1,12,'all');assert.equal(noCachedRows.items.length,0);
});
test('empty and filtered server pages do not hide local samples or change their indices',()=>{
 const onlySamples=pagedLibraryPage(recordings,[],0,'',1,6,'all');assert.equal(onlySamples.total,3);assert.deepEqual(onlySamples.items.map(x=>x.index),[2,1,0]);
 const generated=pagedLibraryPage(recordings,['11'],1,'Exact text 11',1,6,'generated');assert.equal(generated.total,1);assert.equal(generated.items[0].index,11);
 assert.equal(pagedLibraryPage(recordings,[],0,'missing',1,6,'all').total,0);assert.equal(pagedLibraryPage(recordings,[],0,'',99,6,'all').page,1);
});
