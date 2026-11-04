import {useEffect,useState} from 'react';
import type {CleanupView} from './useCleanups';
import {request} from './useStudioBackend';

interface HistoryPage {items:CleanupView[];total:number;page:number;size:number}
export function useCleanupHistoryPage(query:string,page:number,version:number,register:(items:CleanupView[])=>void){
  const [retry,setRetry]=useState(0),key=JSON.stringify([query,page,retry]);
  const [result,setResult]=useState<{key:string;data?:HistoryPage;error?:boolean}>();
  useEffect(()=>{
    let active=true;
    const timer=setTimeout(()=>{
      const params=new URLSearchParams({query,page:String(page),size:'6'});
      void request<HistoryPage>(`/api/cleanups/history?${params}`).then(data=>{
        if(!active)return;
        register(data.items);setResult({key,data});
      }).catch(()=>{if(active)setResult({key,error:true});});
    },query?180:0);
    return()=>{active=false;clearTimeout(timer);};
  },[key,query,page,version,register]);
  const current=result?.key===key?result:undefined;
  return {data:current?.data,error:!!current?.error,loading:!current,retry:()=>setRetry(value=>value+1)};
}
