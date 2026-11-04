import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { MagnifyingGlass, Trash, X, CaretLeft, CaretRight } from '@phosphor-icons/react';
import { AudioPlayer } from './AudioPlayer';
import { Select } from './Select';
import { translator } from './i18n';
import { voicePage } from './voice-catalog';
import type { Locale, VoiceProfile } from './types';

function DeleteVoiceDialog({voice,locale,onDelete,onClose}:{voice:VoiceProfile;locale:Locale;onDelete:(id:string)=>Promise<void>;onClose:()=>void}) {
  const t=translator(locale),dialog=useRef<HTMLDialogElement>(null),cancel=useRef<HTMLButtonElement>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  useEffect(()=>{
    const previous=document.activeElement as HTMLElement|null;
    const element=dialog.current;
    element?.showModal();
    cancel.current?.focus({preventScroll:true});
    const overflow=document.body.style.overflow;document.body.style.overflow='hidden';
    return ()=>{element?.close();document.body.style.overflow=overflow;if(previous?.isConnected)previous.focus({preventScroll:true});};
  },[]);
  const remove=async()=>{
    setBusy(true);setError('');
    try{await onDelete(voice.id);onClose();}
    catch(cause){setError(cause instanceof Error?cause.message:t('voiceDeleteFailed'));setBusy(false);}
  };
  return createPortal(<dialog ref={dialog} className="voice-delete-dialog" aria-labelledby="delete-voice-title" aria-describedby="delete-voice-help" onCancel={event=>{event.preventDefault();if(!busy)onClose();}} onClick={event=>{if(event.target===dialog.current && !busy){const r=dialog.current.getBoundingClientRect();if(event.clientX<r.left || event.clientX>r.right || event.clientY<r.top || event.clientY>r.bottom)onClose();}}}>
    <div className="voice-delete-heading"><h2 id="delete-voice-title">{t('deleteVoiceTitle')}</h2><button type="button" className="quiet icon-button" aria-label={t('close')} disabled={busy} onClick={onClose}><X aria-hidden="true" size={20}/></button></div>
    <p className="voice-delete-name">{voice.name}</p><p id="delete-voice-help">{t('deleteVoiceHelp')}</p>
    {error && <p className="field-error" role="alert">{error}</p>}
    <div className="voice-delete-actions"><button ref={cancel} type="button" className="quiet" disabled={busy} onClick={onClose}>{t('cancel')}</button><button type="button" className="primary destructive" disabled={busy} aria-busy={busy} onClick={()=>void remove()}><Trash aria-hidden="true" size={18}/>{t(busy?'deletingVoice':'deleteVoice')}</button></div>
  </dialog>,document.body);
}

export function VoiceCatalog({voices,locale,online,blockedIds,useVoice,deleteVoice,pausePlayback}:{voices:VoiceProfile[];locale:Locale;online:boolean;blockedIds:string[];useVoice:(id:string)=>void;deleteVoice:(id:string)=>Promise<void>;pausePlayback:(except?:HTMLAudioElement)=>void}) {
  const t=translator(locale);
  const [query,setQuery]=useState(''),[page,setPage]=useState(1),[size,setSize]=useState(12);
  const [deleting,setDeleting]=useState<VoiceProfile|null>(null),[removed,setRemoved]=useState('');
  const results=voicePage(voices,query,page,size,locale);
  const search=useRef<HTMLInputElement>(null),heading=useRef<HTMLDivElement>(null);
  useEffect(()=>{if(page!==results.page)setPage(results.page);},[page,results.page]);
  const go=(next:number)=>{
    pausePlayback();setPage(next);
    requestAnimationFrame(()=>{heading.current?.scrollIntoView({block:'start',behavior:'instant'});heading.current?.focus({preventScroll:true});});
  };
  const language=(code:string)=>{if(code==='auto')return t('auto');try{return new Intl.DisplayNames([locale],{type:'language'}).of(code) ?? code;}catch{return code;}};
  return <section className="voice-catalog" aria-label={t('voices')}>
    <p className="voice-catalog-notice" role="status">{removed?`${t('voiceDeleted')}: ${removed}`:''}</p>
    {!!voices.length && <div className="voice-browser-toolbar">
      <label className="voice-search" htmlFor="voice-search"><span>{t('searchVoices')}</span><div><MagnifyingGlass size={18} aria-hidden="true"/><input ref={search} id="voice-search" type="search" aria-label={t('searchVoices')} value={query} maxLength={200} placeholder={t('searchVoicesPlaceholder')} onChange={event=>{pausePlayback();setQuery(event.target.value);setPage(1);}}/>{query && <button type="button" className="icon-button" aria-label={t('clearVoiceSearch')} onClick={()=>{pausePlayback();setQuery('');setPage(1);search.current?.focus();}}><X aria-hidden="true" size={18}/></button>}</div></label>
      <div className="voice-page-size"><span>{t('voicesPerPage')}</span><Select label={t('voicesPerPage')} value={String(size)} onChange={value=>{pausePlayback();setSize(Number(value));setPage(1);}} options={[6,12,24].map(value=>({value:String(value),label:String(value)}))}/></div>
    </div>}
    <div className="voice-results" ref={heading} tabIndex={-1}><span role="status" aria-live="polite">{t('voicesFound')}: {results.total}{query && ` / ${voices.length}`}</span>{results.total>0 && <span>{t('rangeFrom')} {results.from} {t('rangeTo')} {results.to}</span>}</div>
    <div className="voice-grid">{results.items.map(voice=><article className="voice-profile" key={voice.id} aria-labelledby={`voice-${voice.id}`}>
      <div className="voice-profile-heading"><span className="avatar" aria-hidden="true">{voice.name.slice(0,1).toUpperCase()}</span><div><h2 id={`voice-${voice.id}`}>{voice.name}</h2><p>{language(voice.language)}{voice.duration>0 && ` / ${Math.round(voice.duration*10)/10} ${locale==='ru'?'с':'s'}`}</p></div></div>
      <AudioPlayer src={voice.referenceUrl} label={`${t('reference')} — ${voice.name}`} locale={locale} onPlay={pausePlayback}/>
      <details className="take-source"><summary>{t('referenceText')}</summary><p>{voice.referenceText}</p></details>
      <div className="voice-card-actions"><button type="button" className="quiet" onClick={()=>useVoice(voice.id)}>{t('useVoice')}</button><button type="button" className="quiet icon-button voice-remove" disabled={!online || blockedIds.includes(voice.id)} aria-label={`${t('deleteVoice')} — ${voice.name}`} aria-describedby={blockedIds.includes(voice.id)?`voice-busy-${voice.id}`:undefined} onClick={()=>setDeleting(voice)}><Trash aria-hidden="true" size={19}/></button></div>
      {blockedIds.includes(voice.id) && <p className="setting-help" id={`voice-busy-${voice.id}`}>{t('voiceDeleteBusy')}</p>}
    </article>)}</div>
    {!results.total && (query ? <div className="voice-empty"><h2>{t('noVoicesFound')}</h2><p>{t('voiceSearchHelp')}</p><button type="button" className="quiet" onClick={()=>{pausePlayback();setQuery('');setPage(1);search.current?.focus();}}>{t('clearVoiceSearch')}</button></div> : <p className="empty-copy">{t('noVoices')}</p>)}
    {results.pages>1 && <nav className="voice-pagination" aria-label={t('voicesPagination')}><button type="button" className="quiet" disabled={results.page===1} aria-label={t('previousPage')} onClick={()=>go(results.page-1)}><CaretLeft aria-hidden="true" size={18}/></button><span>{t('page')} {results.page} {t('pageOf')} {results.pages}</span><button type="button" className="quiet" disabled={results.page===results.pages} aria-label={t('nextPage')} onClick={()=>go(results.page+1)}><CaretRight aria-hidden="true" size={18}/></button></nav>}
    {deleting && <DeleteVoiceDialog voice={deleting} locale={locale} onClose={()=>setDeleting(null)} onDelete={async id=>{pausePlayback();await deleteVoice(id);setRemoved(deleting.name);requestAnimationFrame(()=>(search.current ?? heading.current)?.focus());}}/>}
  </section>;
}
