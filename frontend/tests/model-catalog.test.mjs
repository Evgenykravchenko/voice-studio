import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { catalogFilters, modelMatches, modelBytes, modelLanguages, modelLanguageOptions, canonicalLanguage } from '../src/model-catalog.ts';
const model = {name:'Whisper Small',repo:'mlx-community/whisper-small',format:'MLX Q4',task:'transcription',installed:false,status:'downloading'};
test('model filters combine name, task and installation state', () => {
  assert.equal(modelMatches(model,' whisper ','transcription','downloads'),true);
  assert.equal(modelMatches(model,'','synthesis','all'),false);
  assert.equal(modelMatches(model,'','all','installed'),false);
  assert.equal(modelMatches({...model,installed:true,status:'installed'},'q4','all','installed'),true);
  assert.equal(modelMatches(model,'unknown','all','all'),false);
});
test('disk sizes use decimal file units and locale formatting', () => {
  assert.equal(modelBytes(6734508010,'en'),'6.73 GB');
  assert.equal(modelBytes(80474075,'ru'),'80 МБ');
});

test('shared filter URLs preserve valid choices and recover from unknown values', () => {
  assert.deepEqual(catalogFilters('?view=models&q=Whisper&task=transcription&status=installed'), {query:'Whisper',task:'transcription',status:'installed',language:'all',feature:'all',integration:'all'});
  assert.deepEqual(catalogFilters('?task=unknown&status=unknown'), {query:'',task:'all',status:'all',language:'all',feature:'all',integration:'all'});
});

test('Russian, capability and runtime filters do not mistake downloaded weights for connected engines', () => {
  const voice = {...model,task:'synthesis',languages:['ru','en'],features:['cloning'],integration:'files',installed:true};
  assert.equal(modelMatches(voice,'','all','all','ru','cloning','other'),true);
  assert.equal(modelMatches(voice,'','all','all','ru','cloning','ready'),false);
  assert.equal(modelMatches(voice,'','all','all','ru','presets','all'),false);
  assert.equal(modelMatches({...voice,languages:['en']},'','all','all','ru'),false);
  assert.equal(modelBytes(null,'en'),'See source');
  assert.equal(modelLanguages(['en','ru','zh'],'ru'),'русский, английский +1');
});

test('catalog language links survive reload and filter models beyond Russian and English', () => {
  for (const language of ['ja', 'zh', 'hi', 'ar', 'yue', 'pt-br']) {
    const filters = catalogFilters('?view=models&language=' + language);
    assert.equal(filters.language, language);
    assert.equal(modelMatches({...model,languages:[language]}, '', 'all', 'all', filters.language), true);
    assert.equal(modelMatches({...model,languages:['ru','en']}, '', 'all', 'all', filters.language), false);
  }
  for (const language of ['../ja', '<script>', 'auto', 'a'.repeat(200)]) {
    assert.equal(catalogFilters('?language=' + encodeURIComponent(language)).language, 'all');
  }
});

test('catalog language choices come from the full catalog and retain a selected link while loading', () => {
  const rows = [{languages:['ja','en','hi']},{languages:['ru','en','ja','yue']},{languages:[]}];
  const russian = modelLanguageOptions(rows, 'ru');
  assert.deepEqual(russian.slice(0,2).map(x=>x.value), ['ru','en']);
  assert.deepEqual(new Set(russian.map(x=>x.value)), new Set(['ja','en','hi','ru','yue']));
  assert.equal(russian.find(x=>x.value==='ja').label, 'Японский');
  assert.equal(modelLanguageOptions(rows,'en').find(x=>x.value==='ja').label, 'Japanese');
  assert.deepEqual(modelLanguageOptions([], 'en', 'ja'), [{value:'ja',label:'Japanese'}]);
  assert.deepEqual(modelLanguageOptions([], 'ru'), []);
});

test('every declared model language can be selected and restored from a shared link', () => {
  const catalog = JSON.parse(readFileSync(new URL('../../src/voice_cloner/model-catalog.json', import.meta.url), 'utf8'));
  const codes = new Set(catalog.flatMap(model=>model.languages).filter(code=>code!=='auto').map(canonicalLanguage));
  assert.deepEqual(new Set(modelLanguageOptions(catalog,'en').map(x=>x.value)), codes);
  for (const code of catalog.flatMap(model=>model.languages)) assert.equal(catalogFilters('?view=models&language='+encodeURIComponent(code)).language,canonicalLanguage(code));
  for (const locale of ['ru','en']) {
    const options = modelLanguageOptions(catalog,locale);
    assert.equal(new Set(options.map(x=>x.label)).size,options.length);
  }
});

test('language aliases find all matching models without changing native catalog codes', () => {
  const source = {...model,languages:['ara','jpn','eng']};
  for (const language of ['ar','ara','arb']) {
    assert.equal(catalogFilters('?language='+language).language,'ar');
    assert.equal(modelMatches(source,'','all','all',language),true);
  }
  assert.equal(modelMatches(source,'','all','all','ja'),true);
  assert.deepEqual(modelLanguageOptions([source,{languages:['ar','ja','en']}],'en').map(x=>x.value).sort(),['ar','en','ja']);
  assert.deepEqual(source.languages,['ara','jpn','eng']);
});
