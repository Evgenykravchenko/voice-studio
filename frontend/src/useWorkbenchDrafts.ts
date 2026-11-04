import {useCallback,useRef,useState} from 'react';
import type {TranslationKey} from './i18n';

interface Draft {file:File|null;fileError?:TranslationKey;voiceId:string;text:string;duration:string;jobId:string|null;busy:boolean;error:string}
const empty:Draft={file:null,voiceId:'',text:'',duration:'6',jobId:null,busy:false,error:''};

/** Session-only tool drafts retain File objects; recordings stay on the server. */
export function useWorkbenchDrafts(){
  const [activeId,setActiveId]=useState<string|null>(null),[drafts,setDrafts]=useState<Record<string,Draft>>({});
  const positions=useRef(new Map<string,{jobId:string;seconds:number}>());
  const update=useCallback((id:string,patch:Partial<Draft>)=>setDrafts(previous=>({...previous,[id]:{...empty,...previous[id],...patch}})),[]);
  const remember=useCallback((id:string,jobId:string,seconds:number)=>{positions.current.set(id,{jobId,seconds});},[]);
  return {activeId,open:setActiveId,close:()=>setActiveId(null),get:(id:string)=>drafts[id]??empty,update,remember,
    position:(id:string,jobId:string)=>{const value=positions.current.get(id);return value?.jobId===jobId?value.seconds:0;}};
}
