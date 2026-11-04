import { test } from 'node:test';
import assert from 'node:assert/strict';
import { filterSelectOptions } from '../src/select-search.ts';

test('language search accepts localized names, codes and unaccented text', () => {
  const rows = [{value:'jv',label:'Javanese'},{value:'ja',label:'Japanese'},{value:'nb',label:'Норвежский букмол'},{value:'es',label:'Español'}];
  assert.equal(filterSelectOptions(rows,'ja')[0].value,'ja');
  assert.deepEqual(filterSelectOptions(rows,'  японский  '),[]);
  assert.deepEqual(filterSelectOptions(rows,'норвежскии nb').map(x=>x.value),['nb']);
  assert.deepEqual(filterSelectOptions(rows,'espanol').map(x=>x.value),['es']);
  assert.equal(filterSelectOptions(rows,'   '),rows);
  assert.deepEqual(filterSelectOptions(rows,'unknown language'),[]);
  assert.deepEqual(rows.map(x=>x.value),['jv','ja','nb','es']);
});
