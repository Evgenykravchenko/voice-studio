import {useEffect,useRef,useState} from 'react';
import type {useProjects} from './useProjects';
import {audioSignature} from './assembly-utils';
import {useAudioPreferences} from './AudioPreferences';
export interface AssemblySpan {sceneId:string;sourceId:string;start:number;end:number;trimStart:number;trimEnd:number;appliedGainDb:number}
export interface AssemblyResult {duration:number;sampleRate:number;peaks:number[];spans:AssemblySpan[]}
export interface AssemblyTask {id:string;projectId:string;status:string;error:string|null;result:AssemblyResult|null}
async function request(url:string,options?:RequestInit){const response=await fetch(url,{...options,signal:AbortSignal.timeout(15000)});const data=await response.json();if(!response.ok)throw new Error(data.error??'Audio assembly failed.');return data as AssemblyTask;}
export function useAssembly(projects:ReturnType<typeof useProjects>,pauseOthers:(except?:HTMLAudioElement)=>void,ru:boolean){
  const signature=audioSignature(projects.project),identity=`${projects.id}:${signature}`;
  const latest=useRef(identity);latest.current=identity;
  const intent=useRef(0);
  const media=useRef<HTMLAudioElement>(null),stopAt=useRef<number|undefined>(undefined),pendingTime=useRef<number|undefined>(undefined);
  const [task,setTask]=useState<AssemblyTask|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[playing,setPlaying]=useState(false),[elapsed,setElapsed]=useState(0),[active,setActive]=useState(false);
  const ready=useRef<{identity:string;task:AssemblyTask}|null>(null),inflight=useRef<{identity:string;promise:Promise<AssemblyTask>}|null>(null);
  const {preferences:{volume,muted}}=useAudioPreferences();
  useEffect(()=>{if(media.current){media.current.volume=volume;media.current.muted=muted;}},[volume,muted]);
  useEffect(()=>{intent.current++;media.current?.pause();setActive(false);setElapsed(0);setError('');setTask(null);stopAt.current=undefined;},[identity]);
  useEffect(()=>{if(!playing)return;let frame=0;const sync=()=>{const el=media.current;if(el){if(stopAt.current!==undefined && el.currentTime>=stopAt.current){el.pause();stopAt.current=undefined;}setElapsed(el.currentTime);}frame=requestAnimationFrame(sync);};frame=requestAnimationFrame(sync);return()=>cancelAnimationFrame(frame);},[playing]);
  const url=(t:AssemblyTask,format='wav')=>`/api/projects/${t.projectId}/assembly/${t.id}/audio.${format}`;
  const build=async()=>{
    if(ready.current?.identity===identity){setTask(ready.current.task);return ready.current.task;}
    if(inflight.current?.identity===identity)return inflight.current.promise;
    const current=identity;setBusy(true);setError('');
    const promise=(async()=>{
      await projects.flush();const saved=projects.getSnapshot();
      if(saved.status!=='saved' || !saved.id)throw new Error(ru?'Сначала сохраните проект на сервере.':'Save the project to the server first.');
      if(`${saved.id}:${audioSignature(saved.project)}`!==current)throw new Error(ru?'Монтаж изменился. Повторите сборку.':'The montage changed. Build again.');
      let next=await request(`/api/projects/${saved.id}/assembly`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:saved.revision})});
      const deadline=Date.now()+660000;
      while(['queued','running'].includes(next.status)){
        if(latest.current!==current)throw new Error(ru?'Монтаж изменён. Соберите новый итог.':'The montage changed. Build the updated version.');
        if(Date.now()>deadline)throw new Error(ru?'Сборка ещё выполняется. Попробуйте позже.':'Assembly is still running. Try again later.');
        setTask(next);await new Promise(resolve=>setTimeout(resolve,700));next=await request(`/api/projects/${saved.id}/assembly/${next.id}`);
      }
      if(next.status!=='succeeded' || !next.result)throw new Error(next.error??(ru?'Не удалось собрать аудио.':'Audio assembly failed.'));
      if(latest.current!==current)throw new Error(ru?'Монтаж изменён. Соберите новый итог.':'The montage changed. Build the updated version.');
      ready.current={identity:current,task:next};setTask(next);return next;
    })();inflight.current={identity:current,promise};
    try{return await promise;}finally{if(inflight.current?.promise===promise){inflight.current=null;setBusy(false);}}
  };
  const load=(t:AssemblyTask,seconds:number)=>{const el=media.current!;if(el.getAttribute('src')!==url(t)){pendingTime.current=seconds;el.src=url(t);el.load();}else el.currentTime=seconds;setElapsed(seconds);setActive(true);};
  const perform=async(action:()=>Promise<void>)=>{try{await action();}catch(cause){setError(cause instanceof Error?cause.message:String(cause));}};
  const preview=(seconds?:number,end?:number)=>{const token=++intent.current;return perform(async()=>{const t=await build();if(token!==intent.current)return;const el=media.current!;stopAt.current=end;pauseOthers(el);load(t,seconds??(el.ended?0:Math.min(el.currentTime,t.result!.duration)));await el.play();});};
  const seek=(seconds:number)=>{const token=++intent.current;return perform(async()=>{setElapsed(seconds);const resume=active && !media.current?.paused;const t=await build();if(token!==intent.current)return;stopAt.current=undefined;pauseOthers(media.current!);load(t,Math.max(0,Math.min(t.result!.duration,seconds)));if(resume)await media.current!.play();});};
  const join=(sceneId:string)=>{const token=++intent.current;return perform(async()=>{const t=await build();if(token!==intent.current)return;const i=t.result!.spans.findIndex(s=>s.sceneId===sceneId),span=t.result!.spans[i],next=t.result!.spans[i+1];if(!span || !next)return;await preview(Math.max(span.start,span.end-1.5),Math.min(next.end,next.start+1.5));});};
  const download=(format:'wav'|'mp3')=>perform(async()=>{const t=await build();const a=document.createElement('a');a.href=url(t,format);a.download=`${projects.project.title.replaceAll('/', '-').slice(0,100)||'voice-studio-final'}.${format}`;a.click();});
  const deactivate=()=>{intent.current++;media.current?.pause();setActive(false);};
  const audioProps={ref:media,preload:'metadata' as const,onPlay:()=>setPlaying(true),onPause:()=>setPlaying(false),onEnded:()=>{setPlaying(false);stopAt.current=undefined;},onLoadedMetadata:()=>{if(pendingTime.current!==undefined && media.current){media.current.currentTime=pendingTime.current;pendingTime.current=undefined;}},onTimeUpdate:()=>{if(media.current){setElapsed(media.current.currentTime);if(stopAt.current!==undefined && media.current.currentTime>=stopAt.current){media.current.pause();stopAt.current=undefined;}}},onError:()=>{setPlaying(false);setError(ru?'Не удалось воспроизвести итог. Повторите сборку.':'Final audio could not play. Build again.');ready.current=null;}};
  return {prepare:build,task,result:task?.result,busy,error,playing,elapsed,active,media,audioProps,preview,seek,join,download,deactivate,pause:()=>{intent.current++;media.current?.pause();}};
}
