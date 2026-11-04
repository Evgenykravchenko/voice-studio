import { useEffect, useRef, useState } from 'react';
import { FolderOpen, X } from '@phosphor-icons/react';
import { request } from './useStudioBackend';
import { translator } from './i18n';
import type { Locale } from './types';

export function LocalModelImport({id,locale,refresh}:{id:string;locale:Locale;refresh:()=>Promise<unknown>}) {
  const t=translator(locale), input=useRef<HTMLInputElement|null>(null), controller=useRef<AbortController|null>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[progress,setProgress]=useState(0);
  useEffect(()=>()=>controller.current?.abort(),[]);
  const upload=async(files:FileList|null)=>{
    if(!files?.length)return;
    setError('');setBusy(true);setProgress(0);const abort=new AbortController();controller.current=abort;
    try{
      const manifest=await request<{files:{path:string;size:number}[]}>(`/api/models/${id}/manifest`);
      const picked=[...files];const queue=manifest.files.map(expected=>{
        const matches=picked.filter(file=>file.webkitRelativePath.split('/').slice(1).join('/')===expected.path);
        if(matches.length!==1 || matches[0].size!==expected.size)throw new Error(`${t('modelFileMissing')}: ${expected.path}`);
        return {file:matches[0],path:expected.path};
      });
      const total=queue.reduce((sum,item)=>sum+item.file.size,0);let done=0;
      for(const item of queue){
        for(let offset=0;offset<item.file.size;offset+=20*1024*1024){
          if(abort.signal.aborted)return;
          const chunk=item.file.slice(offset,offset+20*1024*1024),body=new FormData();body.append('file',chunk,item.file.name);body.append('path',item.path);body.append('offset',String(offset));
          const response=await fetch(`/api/models/${id}/import/chunk`,{method:'POST',body,signal:abort.signal});
          if(!response.ok){const problem=await response.json().catch(()=>({}));throw new Error(problem.error || t('modelImportFailed'));}
          done+=chunk.size;setProgress(total?done/total:0);
        }
      }
      if(abort.signal.aborted)return;
      await request(`/api/models/${id}/import/complete`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
      await refresh();
    }catch(cause){if(!abort.signal.aborted)setError(cause instanceof Error?cause.message:t('modelImportFailed'));}
    finally{setBusy(false);controller.current=null;if(input.current)input.current.value='';}
  };
  return <div className="local-model-import">
    <p className="setting-help">{t('modelImportHelp')}</p>
    <label className="file-upload-picker"><span className="quiet"><FolderOpen size={18}/>{t(busy?'importingModel':'chooseModelFolder')}</span><input ref={element=>{input.current=element;element?.setAttribute('webkitdirectory','');}} type="file" multiple disabled={busy} aria-label={t('chooseModelFolder')} onChange={event=>void upload(event.target.files)}/></label>
    {busy && <><progress max={1} value={progress} aria-label={t('importingModel')}/><button type="button" className="quiet" onClick={()=>controller.current?.abort()}><X size={16}/>{t('cancelDownload')}</button></>}
    {error && <p className="field-error" role="alert">{error}</p>}
  </div>;
}
