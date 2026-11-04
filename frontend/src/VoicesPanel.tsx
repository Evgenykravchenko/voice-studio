import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Plus, UploadSimple, X, Check, Microphone } from '@phosphor-icons/react';
import { FileUpload } from './FileUpload';
import { canTranscribeLanguage, referenceLanguageOptions, validateVoiceForm, validateVoiceReview, type VoiceErrors, type VoiceField } from './voice-form';
import { AudioPlayer } from './AudioPlayer';
import { VoiceCatalog } from './VoiceCatalog';
import {useVoiceDraft} from './useVoiceDraft';
import { Select } from './Select';
import { translator } from './i18n';
import { readStored } from './state';
import { request } from './useStudioBackend';
import type { Locale, VoiceImport, VoiceProfile } from './types';

function ReviewVoice({ task, locale, onSaved, onDiscard, pausePlayback }: { task: VoiceImport; locale: Locale; onSaved: () => Promise<void>; onDiscard: (id: string) => Promise<void>; pausePlayback: (except?: HTMLAudioElement) => void }) {
  const t = translator(locale);
  const key = `vs.voice-draft.${task.id}`;
  const [draft] = useState(() => readStored(key, { name: task.name, transcript: task.transcript }, (v): v is { name: string; transcript: string } => !!v && typeof v === 'object' && typeof (v as {name?: unknown}).name === 'string' && typeof (v as {transcript?: unknown}).transcript === 'string'));
  const [name, setName] = useState(draft.name), [transcript, setTranscript] = useState(draft.transcript);
  useEffect(() => { try { localStorage.setItem(key, JSON.stringify({ name, transcript })); } catch { /* The original draft remains on the server. */ } }, [key, name, transcript]);
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [fields, setFields] = useState<VoiceErrors>({});
  const form = useRef<HTMLFormElement>(null);
  const nameEdited = useRef(false);
  const reviewField = (field: VoiceField) => setFields(previous => ({ ...previous, [field]: validateVoiceReview(name, transcript)[field] }));
  const save = async (event: FormEvent) => {
    event.preventDefault();
    const invalid = validateVoiceReview(name, transcript); setFields(invalid);
    if (Object.keys(invalid).length) { requestAnimationFrame(() => form.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()); return; }
    setBusy(true); setError('');
    try {
      await request(`/api/voice-imports/${task.id}/save`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, transcript }) });
      try { localStorage.removeItem(key); } catch { /* Storage can be disabled. */ }
      await onSaved();
    } catch (e) { setError(e instanceof Error ? e.message : t('voiceSaveFailed')); }
    finally { setBusy(false); }
  };
  return <form ref={form} className="voice-review" noValidate onSubmit={event => void save(event)}>
    <div className="voice-form-heading"><h2>{t('reviewVoice')}</h2><span>{Math.round(task.duration * 10) / 10} {locale === 'ru' ? 'с' : 's'}</span></div>
    <AudioPlayer src={`/api/voice-imports/${task.id}/reference`} label={`${t('reference')} — ${task.name}`} locale={locale} onPlay={element => pausePlayback(element)} />
    {task.warnings.includes('clipping') && <p className="inline-notice">{t('clippingWarning')}</p>}
    <label>{t('voiceName')} <span className="field-required">{t('required')}</span><input aria-label={t('voiceName')} required maxLength={80} value={name} aria-invalid={!!fields.name} aria-describedby={fields.name ? `review-name-${task.id}` : undefined} onBlur={() => { if (nameEdited.current || fields.name || name.trim()) reviewField('name'); }} onChange={e => { nameEdited.current = true; setName(e.target.value); if (fields.name) setFields(previous => ({ ...previous, name: validateVoiceReview(e.target.value, transcript).name })); }} /></label>
    <p className="field-error field-feedback" aria-live="polite" id={`review-name-${task.id}`}>{fields.name ? t(fields.name) : ''}</p>
    <label>{t('transcript')} <span className="field-required">{t('required')}</span><textarea required maxLength={5000} rows={4} value={transcript} aria-invalid={!!fields.transcript} onBlur={() => reviewField('transcript')} onChange={e => { setTranscript(e.target.value); if (fields.transcript) setFields(previous => ({ ...previous, transcript: validateVoiceReview(name, e.target.value).transcript })); }} aria-describedby={`transcript-help-${task.id}${fields.transcript ? ` transcript-error-${task.id}` : ''}`} /></label>
    {fields.transcript && <p className="field-error" id={`transcript-error-${task.id}`}>{t(fields.transcript)}</p>}
    <p className="setting-help" id={`transcript-help-${task.id}`}>{t('transcriptHelp')}</p>
    {error && <p role="alert" className="generation-error">{error}</p>}
    <div className="voice-form-actions"><button className="primary" disabled={busy} aria-busy={busy} type="submit"><Check size={18} />{t(busy ? 'savingVoice' : 'saveVoice')}</button><button className="quiet" disabled={busy} type="button" onClick={() => { setBusy(true); void onDiscard(task.id).then(() => { try { localStorage.removeItem(key); } catch { /* Storage can be disabled. */ } }).catch(e => { setError(String(e)); setBusy(false); }); }}>{t('discardVoice')}</button></div>
  </form>;
}

export function VoicesPanel({ supportsReferenceLanguages = false, transcriptionLanguages, transcriptionReady, openModels, locale, voices, online, connecting, refreshVoices, deleteVoice, blockedVoiceIds, useVoice, pausePlayback }: { supportsReferenceLanguages?: boolean; transcriptionLanguages: readonly string[]; transcriptionReady: boolean; openModels: () => void; locale: Locale; voices: VoiceProfile[]; online: boolean; connecting: boolean; refreshVoices: () => Promise<void>; deleteVoice: (id: string) => Promise<void>; blockedVoiceIds: string[]; useVoice: (id: string) => void; pausePlayback: (except?: HTMLAudioElement) => void }) {
  const t = translator(locale);
  const {name,setName,file,setFile,start,setStart,duration,setDuration,language,setLanguage}=useVoiceDraft();
  const languageSupported = !transcriptionReady || canTranscribeLanguage(language,transcriptionLanguages) && (supportsReferenceLanguages || ['ru','en','auto'].includes(language));
  const languageHelp = locale==='ru'?'Выбранная модель распознавания не поддерживает язык записи. Выберите другую модель или язык.':'The selected transcription model does not support this recording language. Choose another model or language.';
  const [open, setOpen] = useState(()=>!!name || !!file), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [sourceUrl, setSourceUrl] = useState(''), [tasks, setTasks] = useState<VoiceImport[]>([]), [saved, setSaved] = useState(false);
  const form = useRef<HTMLFormElement>(null);
  const nameEdited = useRef(false);
  const [fields, setFields] = useState<VoiceErrors>({});
  const validateField = (field: VoiceField, patch: Partial<{ name: string; file: File | null; start: string; duration: string }> = {}) => setFields(previous => ({ ...previous, [field]: validateVoiceForm({ name, file, start, duration, ...patch })[field] }));
  const alive = useRef(true);
  useEffect(() => {
    if (!file) { setSourceUrl(''); return; }
    const url = URL.createObjectURL(file); setSourceUrl(url); return () => URL.revokeObjectURL(url);
  }, [file]);
  useEffect(() => {
    alive.current = true; let pending = false;
    const poll = async () => {
      if (!online || pending) return; pending = true;
      try { const values = await request<VoiceImport[]>('/api/voice-imports'); if (alive.current) setTasks(values); }
      catch (e) { if (alive.current) setError(e instanceof Error ? e.message : t('voiceUploadFailed')); }
      finally { pending = false; }
    };
    void poll(); const timer = setInterval(() => void poll(), 1500);
    return () => { alive.current = false; clearInterval(timer); };
  }, [online]);
  const discard = async (id: string) => { await request(`/api/voice-imports/${id}`, { method: 'DELETE' }); setTasks(previous => previous.filter(task => task.id !== id)); };
  const upload = async (event: FormEvent) => {
    event.preventDefault(); setError(''); setSaved(false);
    if (!languageSupported) { setError(languageHelp); return; }
    const invalid = validateVoiceForm({ name, file, start, duration }); setFields(invalid);
    if (Object.keys(invalid).length || !file) { requestAnimationFrame(() => form.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()); return; }
    const body = new FormData(); body.set('file', file); body.set('name', name.trim()); body.set('start', start); body.set('duration', duration); body.set('language', language);
    setBusy(true);
    try {
      const task = await request<VoiceImport>('/api/voice-imports', { method: 'POST', body });
      if (!alive.current) return;
      setTasks(previous => [task, ...previous.filter(value => value.id !== task.id)]); setOpen(false); setFile(null); setName('');
      setStart('0'); setDuration('20'); setFields({}); nameEdited.current = false;
    } catch (e) { if (alive.current) setError(e instanceof Error ? e.message : t('voiceUploadFailed')); }
    finally { if (alive.current) setBusy(false); }
  };
  const onSaved = async () => {
    await refreshVoices(); const next = await request<VoiceImport[]>('/api/voice-imports'); setTasks(next); setSaved(true); setError('');
  };
  const active = tasks.some(task => task.status === 'queued' || task.status === 'running');
  return <div className="voices-workbench">
    <div className="voices-toolbar"><p>{t('voicesTotal')}: {voices.length}</p>{!open && <button className="primary" disabled={!online || busy} onClick={() => { setOpen(true); setSaved(false); setError(''); setFields({}); }}><Plus size={18} />{t('createVoice')}</button>}</div>
    {(connecting || !online) && <p className="inline-notice" role="status">{t(connecting ? 'engineConnecting' : 'engineOffline')}</p>}
    {saved && <p className="inline-notice" role="status">{t('voiceSaved')}</p>}
    {error && <p className="generation-error" role="alert">{error}</p>}
    {open && <form ref={form} className="voice-create" noValidate onSubmit={event => void upload(event)}>
      <div className="voice-form-heading"><h2>{t('createVoice')}</h2><button className="quiet icon-button" type="button" disabled={busy} aria-label={t('cancel')} onClick={() => { setOpen(false); setFile(null); setName(''); setStart('0'); setDuration('20'); setFields({}); nameEdited.current = false; setError(''); }}><X size={20} /></button></div>
      <p className="voice-form-help">{t('createVoiceHelp')}</p>
      <fieldset disabled={busy || !online}>
        <label>{t('voiceName')} <span className="field-required">{t('required')}</span><input aria-label={t('voiceName')} autoFocus required maxLength={80} value={name} aria-invalid={!!fields.name} aria-describedby={fields.name ? 'voice-name-error' : undefined} onBlur={() => { if (nameEdited.current || fields.name || name.trim()) validateField('name'); }} onChange={e => { nameEdited.current = true; setName(e.target.value); if (fields.name) validateField('name', { name: e.target.value }); }} placeholder={t('voiceNamePlaceholder')} autoComplete="off" /></label>
        <p className="field-error field-feedback" aria-live="polite" id="voice-name-error">{fields.name ? t(fields.name) : ''}</p>
        <FileUpload id="voice-upload" file={file} locale={locale} disabled={busy || !online} error={fields.file} onChange={next => { setFile(next); setFields(previous => ({ ...previous, file: undefined })); setError(''); }} onError={message => setFields(previous => ({ ...previous, file: message }))} onBlur={() => { if (file) validateField('file'); }} />
        {sourceUrl && <AudioPlayer key={sourceUrl} src={sourceUrl} label={t('voiceFile')} locale={locale} downloadName={file?.name} onPlay={element => pausePlayback(element)} onDuration={length => { if(Number(duration)>length && length>=5)setDuration(String(Math.min(20,Math.round(length*10)/10))); }} />}
        <div className="voice-clip-fields"><label>{t('clipStart')}<input type="number" min={0} max={86400} step={0.1} required value={start} aria-invalid={!!fields.start} aria-describedby={fields.start ? 'voice-start-error' : undefined} onBlur={() => validateField('start')} onChange={e => { setStart(e.target.value); if (fields.start) validateField('start', { start: e.target.value }); }} />{fields.start && <span className="field-error" id="voice-start-error">{t(fields.start)}</span>}</label><label>{t('clipDuration')}<input type="number" min={5} max={30} step={0.1} required value={duration} aria-invalid={!!fields.duration} aria-describedby={fields.duration ? 'voice-duration-error' : undefined} onBlur={() => validateField('duration')} onChange={e => { setDuration(e.target.value); if (fields.duration) validateField('duration', { duration: e.target.value }); }} />{fields.duration && <span className="field-error" id="voice-duration-error">{t(fields.duration)}</span>}</label><label>{t('referenceLanguage')}<Select label={t('referenceLanguage')} value={language} onChange={setLanguage} disabled={busy || !online} options={referenceLanguageOptions(transcriptionLanguages,language,locale,supportsReferenceLanguages,t('auto'))} /></label></div>
        <p className="setting-help">{t('clipHelp')}</p>
        {!languageSupported && <p className="field-error" role="alert">{languageHelp} <button type="button" className="text-link" onClick={openModels}>{t('openModels')}</button></p>}
        <div className="voice-form-actions"><button className="primary" type="submit" disabled={!online || !transcriptionReady || !languageSupported || busy || active} aria-busy={busy}><UploadSimple size={18} />{t(busy ? 'uploadingVoice' : 'prepareVoice')}</button><span className="setting-help">{t(!transcriptionReady ? 'installTranscription' : active ? 'voiceQueueHelp' : 'reviewHint')}{!transcriptionReady && <button type="button" className="text-link" onClick={openModels}>{t('openModels')}</button>}</span></div>
      </fieldset>
    </form>}
    {tasks.map(task => task.status === 'ready' ? <ReviewVoice key={task.id} task={task} locale={locale} onSaved={onSaved} onDiscard={discard} pausePlayback={pausePlayback} /> : <section key={task.id} className="voice-task" aria-label={`${t('preparingVoice')} — ${task.name}`}><Microphone size={24} /><div><h2>{task.name}</h2>{task.status === 'failed' ? <p className="generation-error" role="alert">{task.error}</p> : <p role="status">{t(task.stage === 'queued' ? 'jobQueued' : task.stage === 'converting' ? 'convertingVoice' : task.stage === 'transcribing' ? 'transcribingVoice' : 'jobStarting')}</p>}</div>{task.status === 'failed' && <button className="quiet" onClick={() => void discard(task.id).catch(e => setError(String(e)))}>{t('discardVoice')}</button>}</section>)}
    {(voices.length>0 || online && !connecting) && <VoiceCatalog voices={voices} locale={locale} online={online} blockedIds={blockedVoiceIds} useVoice={useVoice} deleteVoice={deleteVoice} pausePlayback={pausePlayback}/>}

  </div>;
}
