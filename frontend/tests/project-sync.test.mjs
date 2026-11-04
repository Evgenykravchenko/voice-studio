import {test} from 'node:test';
import assert from 'node:assert/strict';
import {ProjectSync,ProjectRequestError,equalProject,mergeServerTakes} from '../src/project-sync.ts';
const copy=value=>structuredClone(value);
const memory=()=>{const m=new Map();return {getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,v),entries:m};};
const draft=text=>({title:'Test project',scenes:[{id:'scene-a',title:'Intro',text,speechLanguage:'ru',emotion:'calm',temperature:.8,seed:'',audioIndex:null,voiceId:'voice-a'}]});
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
function server(){
 const rows=new Map();let online=true,delay=null;let saves=0;const migration=new Map();
 const transport=async(url,init)=>{
  if(!online)throw new TypeError('Offline');
  const data=init?.body?JSON.parse(init.body):null;
  if(url==='/api/projects' && !init?.method)return [...rows.values()].reverse().map(r=>({id:r.id,revision:r.revision,title:r.project.title,sceneCount:r.project.scenes.length,createdAt:r.createdAt,updatedAt:r.updatedAt}));
  if(url==='/api/projects/migrate'){
   const key=JSON.stringify(data.project);if(migration.has(key))return copy(rows.get(migration.get(key)));
   const id=crypto.randomUUID();const row={id,revision:1,createdAt:'2026-01-01T00:00:00Z',updatedAt:'2026-01-01T00:00:00Z',project:data.project};rows.set(id,row);migration.set(key,id);return copy(row);
  }
  if(url==='/api/projects' && init?.method==='POST'){
   if(rows.has(data.id))return copy(rows.get(data.id));
   const row={id:data.id,revision:1,createdAt:'2026-01-01T00:00:00Z',updatedAt:'2026-01-01T00:00:00Z',project:data.project};rows.set(data.id,row);return copy(row);
  }
  const id=url.split('/').at(-1),row=rows.get(id);if(!row)throw new ProjectRequestError(404,'Missing');
  if(init?.method==='PUT'){
   saves++;if(delay){const d=delay;delay=null;d.resolve();await d.release.promise;}
   if(data.revision!==row.revision)throw new ProjectRequestError(409,'Conflict');
   if(data.project.scenes.some(s=>s.text.length>3000))throw new ProjectRequestError(400,'Too long');
   row.project=copy(data.project);row.revision++;return copy(row);
  }
  return copy(row);
 };
 return {rows,transport,setOnline:value=>online=value,delay:()=>{const entered=deferred();const release=deferred();delay={resolve:entered.resolve,release};return {entered:entered.promise,release:release.resolve};},saves:()=>saves};
}
const seed=(s,text='Base')=>{const id=crypto.randomUUID();s.rows.set(id,{id,revision:1,createdAt:'2026-01-01T00:00:00Z',updatedAt:'2026-01-01T00:00:00Z',project:draft(text)});return id;};
const options=(s,storage=memory(),session=memory(),id)=>({transport:s.transport,storage,session,requestedId:id});
test('legacy migration preserves exact text and IDs and leaves the original backup intact',async()=>{
 const s=server(),storage=memory(),session=memory(),legacy=draft('[whisper] Не меняй API.foo(42).\nИ ё тоже.');storage.setItem('vs.project.v1',JSON.stringify(legacy));
 const sync=new ProjectSync(options(s,storage,session));try{await sync.connect();assert.equal(sync.getSnapshot().status,'saved');assert.deepEqual([...s.rows.values()][0].project,legacy);assert.equal(storage.getItem('vs.project.v1'),JSON.stringify(legacy));sync.edit(draft('Changed'));await sync.flush();assert.equal([...s.rows.values()][0].project.scenes[0].text,'Changed');}finally{sync.stop();}
 const fresh=new ProjectSync(options(s));try{await fresh.connect();assert.equal(fresh.getSnapshot().project.scenes[0].text,'Changed');}finally{fresh.stop();}
});
test('typing during an in-flight save serializes the later draft after the first commit',async()=>{
 const s=server();seed(s);const sync=new ProjectSync(options(s));try{await sync.connect();sync.edit(draft('First edit'));const d=s.delay();const saving=sync.flush();await d.entered;sync.edit(draft('Last edit'));d.release();await saving;assert.equal(sync.getSnapshot().project.scenes[0].text,'Last edit');assert.equal([...s.rows.values()][0].project.scenes[0].text,'Last edit');assert.equal(s.saves(),2);assert.equal(sync.getSnapshot().status,'saved');}finally{sync.stop();}
});
test('offline edits survive a reload and save when the connection returns',async()=>{
 const s=server();const id=seed(s),storage=memory(),session=memory();let sync=new ProjectSync(options(s,storage,session,id));await sync.connect();s.setOnline(false);sync.edit(draft('Offline draft'));await assert.rejects(sync.flush());assert.equal(sync.getSnapshot().status,'offline');sync.stop();sync=new ProjectSync(options(s,storage,session,id));try{s.setOnline(true);await sync.connect();assert.equal(sync.getSnapshot().project.scenes[0].text,'Offline draft');assert.equal(s.rows.get(id).project.scenes[0].text,'Offline draft');assert.equal(sync.getSnapshot().status,'saved');}finally{sync.stop();}
});
test('two editors never silently overwrite each other and save-copy retains both versions',async()=>{
 const s=server(),id=seed(s),storage=memory();const a=new ProjectSync(options(s,storage,memory(),id)),b=new ProjectSync(options(s,storage,memory(),id));
 try{await a.connect();await b.connect();b.edit(draft('Server version'));await b.flush();a.edit(draft('Local version'));await assert.rejects(a.flush());assert.equal(a.getSnapshot().status,'conflict');assert.equal(a.getSnapshot().project.scenes[0].text,'Local version');assert.equal(s.rows.get(id).project.scenes[0].text,'Server version');await a.saveCopy();assert.notEqual(a.getSnapshot().id,id);assert.equal(s.rows.size,2);assert.equal(a.getSnapshot().project.scenes[0].text,'Local version');assert.equal(s.rows.get(id).project.scenes[0].text,'Server version');}finally{a.stop();b.stop();}
});
test('server take links merge into a dirty draft without rewriting text or a manual take choice',async()=>{
 const s=server(),id=seed(s);const old=crypto.randomUUID(),chosen=crypto.randomUUID(),added=crypto.randomUUID();const row=s.rows.get(id);row.project.scenes[0].takeIds=[old,chosen];row.project.scenes[0].selectedTakeId=old;
 const sync=new ProjectSync(options(s,memory(),memory(),id));try{await sync.connect();sync.edit(p=>({...p,scenes:p.scenes.map(scene=>({...scene,text:'My exact edit',selectedTakeId:chosen}))}));row.project.scenes[0].takeIds.push(added);row.project.scenes[0].selectedTakeId=added;row.revision++;await sync.flush();const scene=s.rows.get(id).project.scenes[0];assert.equal(scene.text,'My exact edit');assert.equal(scene.selectedTakeId,chosen);assert.deepEqual(scene.takeIds,[old,chosen,added]);assert.equal(sync.getSnapshot().status,'saved');}finally{sync.stop();}
});
test('server validation failure keeps the draft and never reports it as saved',async()=>{
 const s=server();seed(s);const sync=new ProjectSync(options(s));try{await sync.connect();sync.edit(draft('x'.repeat(3001)));await assert.rejects(sync.flush());assert.equal(sync.getSnapshot().status,'error');assert.equal(sync.getSnapshot().project.scenes[0].text.length,3001);assert.equal([...s.rows.values()][0].project.scenes[0].text,'Base');sync.edit(draft('Fixed'));await sync.flush();assert.equal(sync.getSnapshot().status,'saved');}finally{sync.stop();}
});
test('server saves work when browser storage is disabled',async()=>{
 const s=server();seed(s);const broken={getItem:()=>{throw new Error('Disabled');},setItem:()=>{throw new Error('Disabled');}};const sync=new ProjectSync(options(s,broken));try{await sync.connect();sync.edit(draft('Server only'));await sync.flush();assert.equal(sync.getSnapshot().cacheOk,false);assert.equal(sync.getSnapshot().status,'saved');assert.equal([...s.rows.values()][0].project.scenes[0].text,'Server only');}finally{sync.stop();}
});
test('opening a missing project preserves the current draft and selection',async()=>{
 const s=server(),id=seed(s);const sync=new ProjectSync(options(s));try{await sync.connect();const before=sync.getSnapshot();await assert.rejects(sync.open(crypto.randomUUID()));assert.equal(sync.getSnapshot().id,id);assert.deepEqual(sync.getSnapshot().project,before.project);assert.equal(sync.getSnapshot().switching,false);}finally{sync.stop();}
});
test('take-only merge rejects human edits and compares values independent of property order',()=>{
 const base=draft('Base'),local=draft('Local'),remote=draft('Other editor');assert.equal(mergeServerTakes(local,base,remote),null);assert.equal(equalProject({a:1,b:2},{b:2,a:1}),true);
});
test('a late refresh from the previous project cannot replace an opened project',async()=>{
 const s=server(),a=seed(s,'A'),b=seed(s,'B');let block=false;const entered=deferred(),release=deferred();
 const transport=async(url,init)=>{if(block && url===`/api/projects/${a}` && !init?.method){block=false;const response=await s.transport(url,init);entered.resolve();await release.promise;return response;}return s.transport(url,init);};
 const sync=new ProjectSync({...options(s,memory(),memory(),a),transport});try{await sync.connect();block=true;const refresh=sync.refresh();await entered.promise;await sync.open(b);release.resolve();await refresh;assert.equal(sync.getSnapshot().id,b);assert.equal(sync.getSnapshot().project.scenes[0].text,'B');}finally{release.resolve();sync.stop();}
});
test('typing while a new project is being created preserves the newest draft',async()=>{
 const s=server();seed(s,'Previous project');const entered=deferred(),release=deferred();let block=false;
 const transport=async(url,init)=>{if(block && url==='/api/projects' && init?.method==='POST'){block=false;entered.resolve();await release.promise;}return s.transport(url,init);};
 const sync=new ProjectSync({...options(s),transport});try{await sync.connect();block=true;const creation=sync.create(draft('New project'));await entered.promise;const id=sync.getSnapshot().id;sync.edit(draft('Typed during creation'));release.resolve();await creation;await sync.flush();assert.equal(sync.getSnapshot().id,id);assert.equal(s.rows.get(id).project.scenes[0].text,'Typed during creation');assert.equal(s.rows.size,2);}finally{release.resolve();sync.stop();}
});
