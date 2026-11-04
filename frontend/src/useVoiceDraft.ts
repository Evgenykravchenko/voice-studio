import {useEffect,useState} from 'react';
import {readStored} from './state';
interface VoiceDraft {name:string;file:File|null;start:string;duration:string;language:string}
let memoryDraft:VoiceDraft|null=null;
/** Files stay in this tab's memory; only small form fields enter browser storage. */
export function useVoiceDraft(){
 const [draft,setDraft]=useState<VoiceDraft>(()=>memoryDraft??{...readStored('vs.voice-form.v1',{name:'',start:'0',duration:'20',language:'ru'},(v):v is Omit<VoiceDraft,'file'>=>!!v && typeof v==='object' && ['name','start','duration','language'].every(k=>typeof (v as Record<string,unknown>)[k]==='string')),file:null});
 useEffect(()=>{memoryDraft=draft;const {file,...fields}=draft;try{localStorage.setItem('vs.voice-form.v1',JSON.stringify(fields));}catch{/* The tab retains its draft. */}},[draft]);
 const update=<K extends keyof VoiceDraft>(key:K,value:VoiceDraft[K])=>setDraft(previous=>({...previous,[key]:value}));
 return {...draft,setName:(v:string)=>update('name',v),setFile:(v:File|null)=>update('file',v),setStart:(v:string)=>update('start',v),setDuration:(v:string)=>update('duration',v),setLanguage:(v:string)=>update('language',v)};
}
