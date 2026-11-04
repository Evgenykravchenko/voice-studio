import { X, Waveform } from '@phosphor-icons/react';
import { FileUpload } from './FileUpload';
import { AudioPlayer } from './AudioPlayer';
import { Select } from './Select';
import { request } from './useStudioBackend';
import type { useStudioBackend } from './useStudioBackend';
import type { CatalogModel, Locale } from './types';
import { translator } from './i18n';
import type { TranslationKey } from './i18n';
import type {useWorkbenchDrafts} from './useWorkbenchDrafts';

export function ModelWorkbench({ model, locale, backend, workbench, close }: {model:CatalogModel;locale:Locale;backend:ReturnType<typeof useStudioBackend>;workbench:ReturnType<typeof useWorkbenchDrafts>;close:()=>void}) {
  const t=translator(locale), needsAudio=model.adapter !== 'moss-sfx';
  const {file,fileError,voiceId,text,duration,jobId,busy,error}=workbench.get(model.id);
  const setFile=(file:File|null)=>workbench.update(model.id,{file}),setFileError=(fileError?:TranslationKey)=>workbench.update(model.id,{fileError});
  const setVoiceId=(voiceId:string)=>workbench.update(model.id,{voiceId}),setText=(text:string)=>workbench.update(model.id,{text}),setDuration=(duration:string)=>workbench.update(model.id,{duration});
  const setJobId=(jobId:string)=>workbench.update(model.id,{jobId}),setBusy=(busy:boolean)=>workbench.update(model.id,{busy}),setError=(error:string)=>workbench.update(model.id,{error});
  const selectedVoiceId=backend.voices.some(voice=>voice.id===voiceId)?voiceId:backend.voices[0]?.id ?? '';
  const job=backend.jobs.find(job=>job.id===jobId), running=busy || !!job && ['queued','running'].includes(job.status);
  const submit=async()=>{
    setError('');
    if (needsAudio && !file){setFileError('recordingRequired');return;}
    if (!needsAudio && !text.trim()){setError(t('emptyText'));return;}
    if (model.task==='conversion' && !selectedVoiceId){setError(t('voiceMissing'));return;}
    if (!needsAudio && (!Number.isFinite(Number(duration)) || Number(duration)<1 || Number(duration)>30)){setError(t('effectDurationHelp'));return;}
    setBusy(true);
    try {
      let sourceId:string|undefined;
      if(file && needsAudio){const body=new FormData();body.append('file',file);sourceId=(await request<{id:string}>('/api/media',{method:'POST',body})).id;}
      const result=await backend.submit({sceneId:`tool-${crypto.randomUUID()}`,title:model.name,text,modelId:model.id,voiceId:model.task==='conversion'?selectedVoiceId:null,emotion:'calm',language:'auto',seed:null,sourceId,durationSeconds:needsAudio?undefined:Number(duration)});
      setJobId(result.id);
    } catch(cause){setError(cause instanceof Error?cause.message:t('generationFailed'));}
    finally{setBusy(false);}
  };
  return <section className="voice-create model-workbench" aria-labelledby="tool-heading">
    <div className="model-workbench-heading"><h2 id="tool-heading">{model.name}</h2><button type="button" className="quiet icon-button" aria-label={t('close')} onClick={close}><X size={20}/></button></div>
    <p>{t(model.task==='conversion'?'conversionHelp':needsAudio?'enhanceHelp':'effectsHelp')}</p>
    {needsAudio ? <FileUpload id="tool-audio" locale={locale} file={file} disabled={running} error={fileError} onChange={file=>{setFile(file);setFileError(undefined);}} onError={setFileError} onBlur={()=>{}}/>
      : <label>{t('soundDescription')}<textarea rows={4} maxLength={3000} disabled={running} value={text} onChange={e=>setText(e.target.value)} placeholder={t('soundDescriptionPlaceholder')}/></label>}
    {model.task==='conversion' && <label>{t('targetVoice')}<Select label={t('targetVoice')} disabled={running || !backend.voices.length} value={selectedVoiceId} onChange={setVoiceId} options={backend.voices.map(voice=>({value:voice.id,label:voice.name}))}/></label>}
    {!needsAudio && <label>{t('effectDuration')}<input type="number" min="1" max="30" step="1" disabled={running} value={duration} onChange={e=>setDuration(e.target.value)}/></label>}
    {(error || job?.error) && <p className="field-error" role="alert">{error || job?.error}</p>}
    {running && <p role="status">{t(busy?'uploadingAudio':job?.stage==='loading'?'jobLoading':job?.status==='queued'?'jobQueued':'processingAudio')}</p>}
    <button type="button" className="primary" disabled={running || model.task==='conversion' && !backend.voices.length} onClick={()=>void submit()}><Waveform size={20}/>{t(running?'processingAudio':'runModel')}</button>
    {job?.result && <div className="model-tool-result"><h3>{t('processingResult')}</h3><AudioPlayer key={job.id} src={job.result.url} label={model.name} locale={locale} restorePlayback={{seconds:workbench.position(model.id,job.id),playing:false}} onPosition={seconds=>workbench.remember(model.id,job.id,seconds)} downloadName={`${model.id}.wav`} onPlay={current=>document.querySelectorAll('audio').forEach(audio=>{if(audio!==current)audio.pause();})}/></div>}
  </section>;
}
