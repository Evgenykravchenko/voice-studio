import {useEffect,useState} from 'react';
import type {GenerationJob,RecordingPage} from './types';
import {request} from './useStudioBackend';

export function useRecordingPage(query:string,page:number,size:number,source:string,version:string,register:(jobs:GenerationJob[])=>void){
  const [retry,setRetry]=useState(0);
  const key=JSON.stringify([query,page,size,source,version,retry]);
  const [result,setResult]=useState<{key:string;data?:RecordingPage;error?:boolean}>();
  useEffect(()=>{
    if(source==='samples')return;
    let active=true;
    const timer=setTimeout(()=>{
      const params=new URLSearchParams({query,page:String(page),size:String(size)});
      void request<RecordingPage>(`/api/recordings?${params}`).then(data=>{
        if(!active)return;
        register(data.items);setResult({key,data});
      }).catch(()=>{if(active)setResult({key,error:true});});
    },query?180:0);
    return()=>{active=false;clearTimeout(timer);};
  },[key,query,page,size,source,register]);
  const current=result?.key===key?result:undefined;
  return {data:current?.data,error:!!current?.error,loading:source!=='samples' && !current,retry:()=>setRetry(value=>value+1)};
}
