import {useCallback,useEffect,useRef,useState} from 'react';
import {DEFAULT_ENHANCEMENT,type EnhancementSettings} from './enhancement-settings';
import type {GenerationJob} from './types';
import {request} from './useStudioBackend';
export interface CleanupSource {kind:'scene'|'final';projectId:string;sceneId?:string;sourceId?:string;title:string;url?:string}
export interface CleanupView {task:{id:string;kind:'upload'|'scene'|'final';projectId:string|null;sceneId:string|null;originalSourceId:string|null;assemblyId:string|null;sourceId:string;title:string;sourceText:string;createdAt:string;options:EnhancementSettings|null;baseId:string|null};job:GenerationJob;beforeUrl:string;applied:boolean;comparison:{beforeUrl:string;afterUrl:string}|null}
export function useCleanups(){
  const [tasks,setTasks]=useState<CleanupView[]>([]),[selected,setSelected]=useState<string|null>(()=>new URLSearchParams(location.search).get('cleanupId'));
  const [settings,setSettings]=useState<EnhancementSettings>({...DEFAULT_ENHANCEMENT}),settingsOwner=useRef<string|null>(null);
  const [inputMode,setInputMode]=useState<'file'|'microphone'>('file');
  const [pending,setPending]=useState<CleanupSource|null>(null),[file,setFile]=useState<File|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[loading,setLoading]=useState(true);
  const mounted=useRef(true),polling=useRef(false),lastList=useRef(0),active=useRef<string[]>([]);
  const [historyVersion,setHistoryVersion]=useState(0);
  const registerHistory=useCallback((items:CleanupView[])=>{if(!mounted.current)return;setTasks(previous=>{const map=new Map(previous.map(v=>[v.task.id,v]));items.forEach(v=>map.set(v.task.id,v));const next=[...map.values()].sort((a,b)=>b.task.createdAt.localeCompare(a.task.createdAt));active.current=next.filter(v=>['queued','running'].includes(v.job.status)).map(v=>v.task.id);return next;});},[]);
  const merge=(items:CleanupView[])=>{registerHistory(items);if(mounted.current)setHistoryVersion(value=>value+1);};
  const refresh=async()=>{const next=await request<CleanupView[]>('/api/cleanups');merge(next);lastList.current=Date.now();setError('');return next;};
  useEffect(()=>{mounted.current=true;void refresh().catch(e=>setError(String(e.message))).finally(()=>setLoading(false));const timer=setInterval(async()=>{if(polling.current)return;if(!active.current.length && Date.now()-lastList.current<10000)return;polling.current=true;try{if(!active.current.length)await refresh();else{merge(await Promise.all(active.current.map(id=>request<CleanupView>(`/api/cleanups/${id}`))));setError('');}}catch(e){setError(e instanceof Error?e.message:String(e));}finally{polling.current=false;}},1200);return()=>{mounted.current=false;clearInterval(timer);};},[]);
  const select=(id:string|null)=>{setSelected(id);setError('');const url=new URL(location.href);if(id)url.searchParams.set('cleanupId',id);else url.searchParams.delete('cleanupId');history.replaceState(null,'',url);};
  useEffect(()=>{if(selected && !loading && !tasks.some(t=>t.task.id===selected))void request<CleanupView>(`/api/cleanups/${selected}`).then(v=>merge([v])).catch(e=>setError(e.message));},[selected,loading]);
  useEffect(()=>{if(selected && settingsOwner.current!==selected){const task=tasks.find(v=>v.task.id===selected);if(task){setSettings({...(task.task.options??DEFAULT_ENHANCEMENT),noiseReduction:task.task.options?.noiseReduction??100});settingsOwner.current=selected;}}},[selected,tasks]);
  const perform=async(action:()=>Promise<void>)=>{setBusy(true);setError('');try{await action();}catch(e){setError(e instanceof Error?e.message:String(e));}finally{setBusy(false);}};
  const upload=()=>perform(async()=>{if(!file)return;const body=new FormData();body.append('file',file);body.append('settings',JSON.stringify(settings));const view=await request<CleanupView>('/api/cleanups',{method:'POST',body});merge([view]);select(view.task.id);setPending(null);});
  const source=(body:{projectId:string;sceneId?:string;sourceId?:string;assemblyId?:string},kind:'scene'|'final')=>perform(async()=>{const view=await request<CleanupView>(`/api/cleanups/${kind}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,options:settings})});merge([view]);select(view.task.id);setPending(null);});
  const action=(id:string,action:'retry'|'cancel')=>perform(async()=>{const view=await request<CleanupView>(`/api/cleanups/${id}/${action}`,{method:'POST'});merge([view]);select(view.task.id);});
  const tune=()=>perform(async()=>{if(!selected)return;const view=await request<CleanupView>(`/api/cleanups/${selected}/tune`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(settings)});merge([view]);select(view.task.id);});
  const apply=(id:string,revision:number)=>request(`/api/cleanups/${id}/apply`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision})});
  return {show:(id:string)=>{setPending(null);select(id);},settings,setSettings,tune,inputMode,setInputMode,tasks,historyVersion,registerHistory,selected,pending,file,busy,error,loading,current:tasks.find(v=>v.task.id===selected),select,setFile:(file:File|null)=>{if(selected)setSettings({...DEFAULT_ENHANCEMENT});settingsOwner.current=null;setFile(file);setPending(null);select(null);},open:(source:CleanupSource)=>{settingsOwner.current=null;setSettings({...DEFAULT_ENHANCEMENT});setPending(source);select(null);},reset:()=>{setPending(null);select(null);},upload,source,action,apply,refresh,perform};
}
