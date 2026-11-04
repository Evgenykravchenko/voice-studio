import { initialProject, isProject } from './state.ts';
import type { Project } from './types';
import {recentTakeIds} from './take-links.ts';

export interface StoredProject {id:string;revision:number;createdAt:string;updatedAt:string;project:Project}
export interface ProjectSummary {id:string;revision:number;title:string;sceneCount:number;createdAt:string;updatedAt:string}
export type ProjectStatus='loading'|'saved'|'saving'|'offline'|'conflict'|'error';
export interface ProjectSnapshot {project:Project;id:string|null;revision:number;status:ProjectStatus;ready:boolean;switching:boolean;cacheOk:boolean;summaries:ProjectSummary[];error:string}
interface StorageLike {getItem:(key:string)=>string|null;setItem:(key:string,value:string)=>void}
interface Cached {id:string|null;revision:number;project:Project;base:Project;dirty:boolean;needsMigration:boolean;creation?:Project}
export type ProjectTransport=(url:string,init?:RequestInit)=>Promise<unknown>;
export class ProjectRequestError extends Error {status:number;constructor(status:number,message:string){super(message);this.status=status;}}
export async function projectRequest(url:string,init?:RequestInit):Promise<unknown> {
  const response=await fetch(url,{...init,signal:AbortSignal.timeout(10000),cache:'no-store'});
  const value=await response.json().catch(()=>null);
  if(!response.ok)throw new ProjectRequestError(response.status,value?.error || `HTTP ${response.status}`);
  return value;
}
export function equalProject(a:unknown,b:unknown):boolean {
  const canonical=(value:unknown):unknown=>Array.isArray(value)?value.map(canonical):value && typeof value==='object'?Object.fromEntries(Object.entries(value).filter(([,v])=>v!==undefined).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,canonical(v)])):value;
  return JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
}
/** Only server-generated take links are merged automatically. Human text conflicts stay explicit. */
export function mergeServerTakes(local:Project,base:Project,remote:Project):Project|null {
  const withoutTakes=(p:Project)=>({...p,scenes:p.scenes.map(({takeIds,selectedTakeId,...scene})=>scene)});
  if(!equalProject(withoutTakes(base),withoutTakes(remote)))return null;
  return {...local,scenes:local.scenes.map(scene=>{
    const original=base.scenes.find(s=>s.id===scene.id),incoming=remote.scenes.find(s=>s.id===scene.id);
    if(!original || !incoming)return scene;
    const selected=scene.selectedTakeId!==original.selectedTakeId?scene.selectedTakeId:incoming.selectedTakeId;
    const ids=recentTakeIds([...(scene.takeIds??[]),...(incoming.takeIds??[])],selected);
    return {...scene,...(ids.length?{takeIds:ids}:{}),...(selected?{selectedTakeId:selected}:{})};
  })};
}
const uuid=(id:unknown):id is string=>typeof id==='string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id);
function stored(value:unknown):StoredProject {
  const s=value as StoredProject;
  if(!s || !uuid(s.id) || !Number.isInteger(s.revision) || s.revision<1 || !isProject(s.project))throw new Error('Invalid project response');
  return s;
}
function parse(storage:StorageLike|null,key:string):unknown {try{return JSON.parse(storage?.getItem(key)??'null');}catch{return null;}}
function cache(value:unknown):value is Cached {
  const c=value as Cached;return !!c && (c.id===null || uuid(c.id)) && Number.isInteger(c.revision) && c.revision>=0 && isProject(c.project) && isProject(c.base) && typeof c.dirty==='boolean' && typeof c.needsMigration==='boolean' && (c.creation===undefined || isProject(c.creation));
}

export class ProjectSync {
  private listeners=new Set<()=>void>();
  private state:ProjectSnapshot;
  private base:Project;
  private dirty=false;
  private needsMigration=false;
  private creation:Project|undefined;
  private version=0;
  private active=true;
  private connecting:Promise<void>|null=null;
  private saving:Promise<void>|null=null;
  private timer:ReturnType<typeof setTimeout>|undefined;
  private interval:ReturnType<typeof setInterval>|undefined;
  private client:string;
  private transport:ProjectTransport;
  private storage:StorageLike|null;
  private session:StorageLike|null;
  constructor(options:{transport?:ProjectTransport;storage?:StorageLike|null;session?:StorageLike|null;requestedId?:string|null}={}) {
    this.transport=options.transport??projectRequest;
    try{this.storage=options.storage===undefined?localStorage:options.storage;}catch{this.storage=null;}
    try{this.session=options.session===undefined?sessionStorage:options.session;}catch{this.session=null;}
    const priorClient=parse(this.session,'vs.projects.client.v2');this.client=uuid(priorClient)?priorClient:crypto.randomUUID();
    try{this.session?.setItem('vs.projects.client.v2',JSON.stringify(this.client));}catch{this.session=null;}
    const active=options.requestedId??parse(this.session,'vs.projects.active.v2')??parse(this.storage,'vs.projects.active.v2');
    const id=uuid(active)?active:null;
    const saved=parse(this.storage,this.key(id));
    const legacy=parse(this.storage,'vs.project.v1');
    const initial=cache(saved)?saved: {id,revision:0,project:!id&&isProject(legacy)?legacy:structuredClone(initialProject),base:!id&&isProject(legacy)?legacy:structuredClone(initialProject),dirty:!id&&isProject(legacy),needsMigration:!id&&isProject(legacy)};
    this.base=initial.base;this.dirty=initial.dirty;this.needsMigration=initial.needsMigration;this.creation=initial.creation;
    this.state={project:initial.project,id:initial.id,revision:initial.revision,status:'loading',ready:false,switching:false,cacheOk:!!this.storage,summaries:[],error:''};
  }
  private key(id:string|null){return `vs.projects.cache.v2.${id??'local'}.${this.client}`;}
  getSnapshot=()=>this.state;
  subscribe=(fn:()=>void)=>{this.listeners.add(fn);return()=>{this.listeners.delete(fn);};};
  private publish(patch:Partial<ProjectSnapshot>={}) {
    if(!this.active)return;
    this.state={...this.state,...patch};for(const fn of this.listeners)fn();
  }
  private persist() {
    if(!this.active)return;
    const value:Cached={id:this.state.id,revision:this.state.revision,project:this.state.project,base:this.base,dirty:this.dirty,needsMigration:this.needsMigration,...(this.creation?{creation:this.creation}:{})};
    try{
      if(!this.storage)throw new Error('Storage unavailable');
      this.storage.setItem(this.key(this.state.id),JSON.stringify(value));
      if(this.state.id){this.storage.setItem('vs.projects.active.v2',JSON.stringify(this.state.id));this.session?.setItem('vs.projects.active.v2',JSON.stringify(this.state.id));}
      if(!this.state.cacheOk)this.publish({cacheOk:true});
    }catch{if(this.state.cacheOk)this.publish({cacheOk:false});}
  }
  private hydrate(remote:StoredProject) {
    this.base=remote.project;this.dirty=false;this.needsMigration=false;this.creation=undefined;this.version++;
    this.publish({id:remote.id,revision:remote.revision,project:remote.project,status:'saved',ready:true,error:''});this.persist();
  }
  private adopt(remote:StoredProject):boolean {
    if(!this.active)return false;
    if(!this.dirty || equalProject(this.state.project,remote.project)){this.hydrate(remote);return true;}
    const merged=mergeServerTakes(this.state.project,this.base,remote.project);
    if(!merged){this.publish({status:'conflict',ready:true,error:''});return false;}
    this.base=remote.project;this.dirty=!equalProject(merged,remote.project);this.version++;
    this.publish({id:remote.id,revision:remote.revision,project:merged,status:this.dirty?'saving':'saved',ready:true,error:''});this.persist();return true;
  }
  private fail(error:unknown) {
    if(!this.active)return;
    const conflict=error instanceof ProjectRequestError && error.status===409;
    const invalid=error instanceof ProjectRequestError && error.status>=400 && error.status<500 && error.status!==404;
    this.publish({status:conflict?'conflict':invalid?'error':'offline',ready:true,error:error instanceof ProjectRequestError?error.message:''});this.persist();
  }
  private async json(url:string,body:unknown,method='POST',keepalive=false){const data=JSON.stringify(body);return this.transport(url,{method,headers:{'Content-Type':'application/json'},body:data,keepalive:keepalive && new TextEncoder().encode(data).length<60000});}
  private async bootstrap() {
    if(this.state.status==='conflict')return;
    const list=await this.transport('/api/projects') as ProjectSummary[];
    if(!Array.isArray(list))throw new Error('Invalid project list');
    this.publish({summaries:list});
    if(this.state.id) {
      let remote:StoredProject;
      try{remote=stored(await this.transport(`/api/projects/${this.state.id}`));}
      catch(error){
        if(!(error instanceof ProjectRequestError) || error.status!==404 || !this.creation)throw error;
        remote=stored(await this.json('/api/projects',{id:this.state.id,project:this.creation}));
      }
      this.adopt(remote);return;
    }
    if(this.needsMigration || this.dirty) {
      const version=this.version,sent=this.state.project;
      const remote=stored(await this.json('/api/projects/migrate',{project:sent}));
      if(!this.active)return;
      if(this.version===version){this.hydrate(remote);return;}
      this.base=sent;this.needsMigration=false;this.publish({id:remote.id,revision:remote.revision});this.adopt(remote);return;
    }
    if(list.length){this.hydrate(stored(await this.transport(`/api/projects/${list[0].id}`)));return;}
    const id=crypto.randomUUID();this.creation=this.state.project;this.dirty=true;
    this.publish({id,revision:0});this.persist();
    this.adopt(stored(await this.json('/api/projects',{id,project:this.creation})));
  }
  connect=async()=>{
    if(!this.active || this.state.switching || this.state.status==='conflict')return;
    if(this.connecting)return this.connecting;
    if(this.saving)return this.saving;
    this.connecting=this.bootstrap();
    try{await this.connecting;}catch(error){this.fail(error);}
    finally{this.connecting=null;}
    if(this.dirty && this.state.revision>0 && this.getSnapshot().status!=='conflict' && this.getSnapshot().status!=='offline')await this.flush();
  };
  start=()=>{this.active=true;void this.connect().catch(()=>{});this.interval=setInterval(()=>{void this.connect().catch(()=>{});},5000);};
  stop=()=>{this.active=false;clearTimeout(this.timer);clearInterval(this.interval);};
  edit=(update:Project|((previous:Project)=>Project))=>{
    if(!this.state.ready || this.state.switching)return;
    const next=typeof update==='function'?update(this.state.project):update;
    if(equalProject(next,this.state.project))return;
    this.version++;this.dirty=true;if(!this.state.id)this.needsMigration=true;
    this.publish({project:next,status:this.state.status==='conflict'?'conflict':this.state.status==='offline'?'offline':'saving',error:''});this.persist();
    clearTimeout(this.timer);this.timer=setTimeout(()=>{void this.flush().catch(()=>{});},650);
  };
  flush=async(keepalive=false)=>{
    clearTimeout(this.timer);
    if(this.saving)return this.saving;
    if(this.connecting)await this.connecting.catch(()=>{});
    if(!this.dirty)return;
    if(this.state.status==='conflict')throw new ProjectRequestError(409,'Project conflict');
    if(!this.state.id || this.state.revision===0){await this.connect();if(this.dirty)throw new Error('Project unavailable');return;}
    this.saving=this.saveLoop(keepalive);
    try{await this.saving;}finally{this.saving=null;}
  };
  private async saveLoop(keepalive:boolean) {
    let retries=0;
    try{
      while(this.active && this.dirty){
        const id=this.state.id!,revision=this.state.revision,version=this.version,project=this.state.project;
        this.publish({status:'saving',error:''});
        try{
          const remote=stored(await this.json(`/api/projects/${id}`,{revision,project},'PUT',keepalive));
          if(!this.active)return;
          this.base=remote.project;this.creation=undefined;this.needsMigration=false;
          if(version===this.version){this.hydrate(remote);}else{this.publish({revision:remote.revision});this.persist();}
        }catch(error){
          if(error instanceof ProjectRequestError && error.status===409 && retries++<5){const latest=stored(await this.transport(`/api/projects/${id}`));if(this.adopt(latest))continue;}
          throw error;
        }
      }
      void this.refreshList();
    }catch(error){this.fail(error);throw error;}
  }
  refreshList=async()=>{try{const values=await this.transport('/api/projects') as ProjectSummary[];if(Array.isArray(values))this.publish({summaries:values});}catch{/* The current draft stays available. */}};
  refresh=async()=>{
    if(!this.state.id || this.connecting || this.saving || this.state.status==='conflict')return;
    const id=this.state.id;
    try{const remote=stored(await this.transport(`/api/projects/${id}`));if(this.state.id!==id || this.state.switching)return;this.adopt(remote);if(this.dirty)await this.flush();}catch(error){if(this.state.id===id)this.fail(error);}
  };
  open=async(id:string)=>{
    if(this.state.switching)return;
    this.publish({switching:true});
    try{await this.flush();if(this.dirty)throw new Error('Unsaved project');const remote=stored(await this.transport(`/api/projects/${id}`));this.hydrate(remote);}
    finally{this.publish({switching:false});}
  };
  create=async(project:Project)=>{
    if(this.state.switching)return;
    this.publish({switching:true});
    try{
      await this.flush();if(this.dirty)throw new Error('Unsaved project');
      const id=crypto.randomUUID();this.creation=project;this.base=project;this.dirty=true;this.needsMigration=false;this.version++;
      this.publish({id,revision:0,project,status:'saving',ready:true,switching:false});this.persist();
      try{this.adopt(stored(await this.json('/api/projects',{id,project})));await this.refreshList();}
      catch(error){this.fail(error);}
    }finally{this.publish({switching:false});}
  };

  saveCopy=async()=>{
    const project=this.state.project,id=crypto.randomUUID();
    this.publish({switching:true});
    try{const remote=stored(await this.json('/api/projects',{id,project}));this.hydrate(remote);await this.refreshList();}
    finally{this.publish({switching:false});}
  };
  loadServer=async()=>{
    if(!this.state.id)return;
    this.publish({switching:true});
    try{
      if(this.storage)this.storage.setItem(`vs.projects.recovery.v2.${this.state.id}.${this.client}`,JSON.stringify(this.state.project));
      this.hydrate(stored(await this.transport(`/api/projects/${this.state.id}`)));
    }finally{this.publish({switching:false});}
  };
}
