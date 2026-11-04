import {useEffect,useState,useSyncExternalStore} from 'react';
import {ProjectSync} from './project-sync';
export function useProjects(){
  const [sync]=useState(()=>new ProjectSync({requestedId:new URLSearchParams(location.search).get('project')}));
  const state=useSyncExternalStore(sync.subscribe,sync.getSnapshot);
  useEffect(()=>{
    if(state.ready && state.id){const url=new URL(location.href);url.searchParams.set("project",state.id);history.replaceState(null,"",url);}
  },[state.ready,state.id]);
  useEffect(()=>{
    sync.start();
    const focus=()=>{void sync.connect().catch(()=>{});};
    const pop=async()=>{
      const requested=new URLSearchParams(location.search).get('project');
      try{if(requested && sync.getSnapshot().ready && requested!==sync.getSnapshot().id)await sync.open(requested);}catch{/* Keep the current unsaved draft. */}
      const current=sync.getSnapshot().id;
      if(current){const url=new URL(location.href);url.searchParams.set('project',current);history.replaceState(null,'',url);}
    };
    const hidden=()=>{if(document.visibilityState==='hidden')void sync.flush(true).catch(()=>{});else void sync.connect().catch(()=>{});};
    addEventListener('focus',focus);addEventListener('popstate',pop);document.addEventListener('visibilitychange',hidden);
    return()=>{sync.stop();removeEventListener('focus',focus);removeEventListener('popstate',pop);document.removeEventListener('visibilitychange',hidden);};
  },[sync]);
  return {...state,getSnapshot:sync.getSnapshot,setProject:sync.edit,flush:sync.flush,refresh:sync.refresh,refreshList:sync.refreshList,open:sync.open,create:sync.create,retry:sync.connect,saveCopy:sync.saveCopy,loadServer:sync.loadServer};
}
