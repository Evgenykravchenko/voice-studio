import { useEffect, useRef, useState } from 'react';
import { Waveform, Globe, Moon, Sun, Desktop, Check, CaretDown, CaretRight, Plus, DotsThree, Play, Pause, Export, DownloadSimple, X, SlidersHorizontal, FolderOpen, Info, ArrowCounterClockwise, CaretUp, Scissors } from '@phosphor-icons/react';
import type { Icon } from '@phosphor-icons/react';
import type { Emotion, Locale, Recording, Scene, Theme, View } from './types';
import { translator } from './i18n';
import { isLocale, isTheme, readStored } from './state';
import { useStudioBackend } from './useStudioBackend';
import { SeekWave } from './Wave';
import { Select } from './Select';
import { VolumeControl, useAudioPreferences } from './AudioPreferences';
import { VoicesPanel } from './VoicesPanel';
import { useInputModality } from './useInputModality';
import { Menu } from './Menu';
import { ModelsPanel } from './ModelsPanel';
import { useModelCatalog } from './useModelCatalog';
import {useWorkbenchDrafts} from './useWorkbenchDrafts';
import { assignDefaultVoice, resolveVoiceId } from './voices';
import { useProjects } from './useProjects';
import { ProjectsPanel } from './ProjectsPanel';
import {useChromeLayout} from './useChromeLayout';
import {LibraryPanel} from './LibraryPanel';
import {AssemblyPanel} from './AssemblyPanel';
import {ProjectTimeline} from './ProjectTimeline';
import {CleanupPanel} from './CleanupPanel';
import {useCleanups,type CleanupView} from './useCleanups';
import {useAssembly} from './useAssembly';
import {arrangement} from './assembly-utils';
import {resolveSceneSelection} from './scene-selection';
import {sparkDescription,sparkLevels,sparkVoice,type SparkLevel} from './voice-design';
import {insertSpeechTag,insertSpeechPause,type SpeechEdit} from './speech-markup';
import {deliveryEmotions,effectiveDelivery,deliveryLabel} from './delivery';

const tags: Record<Emotion, string> = { calm: '[calm]', excited: '[excited]', whisper: '[whisper]', laughing: '[laughing]', angry: '[angry]' };
const time = (seconds: number) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
const readView = (): View => { const v = new URLSearchParams(location.search).get('view'); return ['projects','voices','models','library','cleanup'].includes(v ?? '') ? v as View : 'studio'; };

export function App() {
  useInputModality();
  const [locale, setLocale] = useState(() => readStored('vs.locale', 'ru', isLocale));
  const [theme, setTheme] = useState(() => readStored('vs.theme', 'dark', isTheme));
  const projects=useProjects();
  const {project,setProject}=projects;
  const backend = useStudioBackend();
  const modelCatalog = useModelCatalog();
  const workbench=useWorkbenchDrafts();
  const cleanups=useCleanups();
  const synthesisModel = modelCatalog.catalog?.models.find(model => model.task === 'synthesis' && model.active);
  const installedSynthesis = modelCatalog.catalog?.models.filter(model => model.task === 'synthesis' && model.ready) ?? [];
  const synthesisReady = !!synthesisModel;
  const synthesisLoading=!modelCatalog.catalog && !modelCatalog.error;
  const fishModel = synthesisModel?.id === 'fish-s2-pro';
  const textLanguage = fishModel || synthesisModel?.languageMode==='text';
  const compactEmotion = synthesisModel?.id==='voxcpm2';
  const availableEmotions = deliveryEmotions(synthesisModel?.id);
  const canDirectEmotion = availableEmotions.length > 0;
  const transcriptionModel = modelCatalog.catalog?.models.find(model => model.task === 'transcription' && model.active);
  const transcriptionReady = !!transcriptionModel;
  const recordings = backend.recordings;
  const { preferences: audioPreferences } = useAudioPreferences();
  const [submitting, setSubmitting] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);

  const [selected, setSelected] = useState(new URLSearchParams(location.search).get('scene') ?? project.scenes[0]?.id ?? '');
  const [view, setView] = useState<View>(readView);
  const [timelineExpanded,setTimelineExpanded]=useState(()=>matchMedia('(min-width: 900px) and (min-height: 601px)').matches);
  const [inspectorExpanded,setInspectorExpanded]=useState(()=>matchMedia('(min-width: 900px)').matches);
  const [miniDismissed,setMiniDismissed]=useState(false);
  const headerRef=useRef<HTMLElement>(null),dockRef=useRef<HTMLElement>(null);
  const [assemblyMode,setAssemblyMode]=useState(()=>new URLSearchParams(location.search).get('mode')==='assembly');
  const [tab, setTab] = useState<'text' | 'markup'>('text');
  const [advanced, setAdvanced] = useState(false);
  const [notice, setNotice] = useState<'backendNotice' | 'emptyText' | 'playbackError' | null>(null);
  const [deleted, setDeleted] = useState<{ scene: Scene; index: number } | null>(null);
  const [playing, setPlaying] = useState(false);
  const [playingIndex, setPlayingIndex] = useState<number | null>(null);
  const shortViewport=useChromeLayout(headerRef,dockRef,`${view}-${timelineExpanded}-${miniDismissed}-${playingIndex!==null}`);
  const timelineOpen=timelineExpanded && !shortViewport;
  const [elapsed, setElapsed] = useState(0);
  const audio = useRef<HTMLAudioElement>(null);
  const pendingSeek = useRef<{ url: string; seconds: number } | null>(null);
  const editor = useRef<HTMLTextAreaElement>(null);
  const t = translator(locale);
  const scene = project.scenes.find(s => s.id === selected) ?? project.scenes[0];
  const deliveryEmotion = effectiveDelivery(synthesisModel?.id,scene?.emotion ?? 'calm');
  const voiceModes=backend.health?.supportsVoiceModes ? synthesisModel?.synthesisModes : undefined;
  const voiceModeFor=(item?:Scene)=>item?.voiceMode && voiceModes?.includes(item.voiceMode) ? item.voiceMode : synthesisModel?.synthesisMode ?? 'clone';
  const voiceMode=voiceModeFor(scene);
  const audioIndexFor = (s: Scene): number | null => {
    if (s.selectedTakeId) { const index = recordings.findIndex(r => r.id === s.selectedTakeId); return index < 0 ? null : index; }
    return s.audioIndex != null && recordings[s.audioIndex]?.available !== false ? s.audioIndex : null;
  };
  useEffect(()=>{
    if(projects.ready)void backend.ensureRecordings([...project.scenes.flatMap(s=>s.selectedTakeId?[s.selectedTakeId]:[]),...(scene?.takeIds??[])]);
  },[projects.ready,project.scenes,scene?.id,backend.ensureRecordings]);
  const sceneAudioIndex = scene ? audioIndexFor(scene) : null;
  const recording = sceneAudioIndex == null ? null : recordings[sceneAudioIndex];
  const sceneTakes = scene ? recordings.map((r, index) => ({ ...r, index })).filter(r => scene.takeIds?.includes(r.id) || !r.generated && scene.audioIndex===r.index && !!scene.takeIds?.length).sort((a,b)=>a.generated && b.generated?(a.createdAt??'').localeCompare(b.createdAt??''):0) : [];
  const sceneJob = backend.jobs.find(j => j.request.projectId === projects.id && j.request.sceneId === scene?.id && (j.status === 'queued' || j.status === 'running'));
  useEffect(() => { if(projects.ready) setProject(previous => assignDefaultVoice(previous, backend.voices)); }, [backend.voices, project.scenes, projects.ready]);
  const selectedVoiceId = resolveVoiceId(scene?.voiceId, backend.voices) ?? '';
  const selectedVoice = backend.voices.find(v => v.id === selectedVoiceId);
  const voiceName = (id?: string | null) => backend.voices.find(v => v.id === id)?.name ?? t(id ? 'voiceUnavailable' : 'chooseVoice');
  const chosenPreset=synthesisModel?.presetVoices?.includes(scene?.presetVoice ?? '') ? scene?.presetVoice : synthesisModel?.presetVoices?.[0];
  const presetLanguage=synthesisModel?.adapter==='kokoro' ? ({a:'en',b:'en',e:'es',f:'fr',h:'hi',i:'it',j:'ja',p:'pt',z:'zh'} as Record<string,string>)[chosenPreset?.[0] ?? 'a'] : undefined;
  const effectiveLanguage=textLanguage ? 'auto' : presetLanguage ?? (synthesisModel?.languages.length===1 ? synthesisModel.languages[0] : scene?.speechLanguage==='auto' && synthesisModel?.autoLanguage!==false || synthesisModel?.languages.includes(scene?.speechLanguage ?? '') ? scene.speechLanguage : synthesisModel?.languages.includes('en') ? 'en' : synthesisModel?.languages[0] ?? 'auto');
  const fixedSpeechLanguage=textLanguage || !!presetLanguage || synthesisModel?.languages.length===1;
  const recordingVoiceName = (item: Recording) => item.generated ? item.presetVoice ?? (item.voiceDescription ? t('voiceDescription') : !item.voiceId && item.modelId ? modelCatalog.catalog?.models.find(model=>model.id===item.modelId)?.name ?? t('processing') : voiceName(item.voiceId)) : t('demoVoice');
  const controlledVoice=synthesisModel?.voiceDesignControls==='spark';
  const sparkSettings=sparkVoice(scene?.voiceDescription);
  const designDescription=controlledVoice?sparkDescription(sparkSettings):scene?.voiceDescription;
  const designLabel=controlledVoice?t('controlledVoice'):t('designVoice');
  const sceneVoiceLabel=(item:Scene)=>voiceModeFor(item)==='design'?designLabel:voiceModeFor(item)==='preset'?(synthesisModel?.presetVoices?.includes(item.presetVoice??'')?item.presetVoice:synthesisModel?.presetVoices?.[0])??t('readyVoice'):voiceName(resolveVoiceId(item.voiceId,backend.voices));
  const voiceReady = voiceMode === 'clone' ? !!selectedVoice : voiceMode === 'design' ? !!designDescription?.trim() : !!synthesisModel?.presetVoices?.length;
  const referenceAudio = useRef<HTMLAudioElement>(null);
  const [previewingVoice, setPreviewingVoice] = useState(false);
  useEffect(() => { for (const element of [audio.current, referenceAudio.current]) { if (element) { element.volume = audioPreferences.volume; element.muted = audioPreferences.muted; } } }, [audioPreferences]);
  const pauseAllPlayback = (except?: HTMLAudioElement):void => { if(except!==montage.media.current)montage.deactivate();document.querySelectorAll<HTMLAudioElement>('audio').forEach(el=>{if(el!==except)el.pause();}); };
  const montage=useAssembly(projects,pauseAllPlayback,locale==='ru');
  const assemblyItems=arrangement(project,recordings);
  const assemblyReady=assemblyItems.some(i=>!i.excluded && i.recording) && !assemblyItems.some(i=>!i.excluded && (!i.recording || !i.edit || i.duration<.08-1e-6 || i.edit.end>i.recording.duration+.025));
  const setAssembly=(value:boolean)=>{setAssemblyMode(value);const url=new URL(location.href);value?url.searchParams.set('mode','assembly'):url.searchParams.delete('mode');history.replaceState(null,'',url);};
  useEffect(() => { referenceAudio.current?.pause(); }, [selectedVoiceId]);
  const previewSelectedVoice = async () => {
    const el = referenceAudio.current; if (!el || !selectedVoice) return;
    if (!el.paused) { el.pause(); return; }
    pauseAllPlayback(); el.src = selectedVoice.referenceUrl;
    try { await el.play(); } catch { setNotice('playbackError'); }
  };
  const reconciledJobs=useRef(new Set<string>());
  useEffect(() => {
    if(!projects.id || !projects.ready)return;
    const incoming=backend.jobs.filter(job=>job.request.projectId===projects.id && job.status==='succeeded' && !reconciledJobs.current.has(job.id));
    if(incoming.length){incoming.forEach(job=>reconciledJobs.current.add(job.id));void projects.refresh();}
  },[backend.jobs,project.scenes,projects.id,projects.ready]);
  const priorProject=useRef(projects.id);
  useEffect(()=>{
    if(priorProject.current && priorProject.current!==projects.id){
      pauseAllPlayback();setPlayingIndex(null);setElapsed(0);setDeleted(null);
    }
    priorProject.current=projects.id;
  },[projects.id]);
  const generate = async () => {
    if (!scene?.text.trim()) { setNotice('emptyText'); return; }
    const seed = scene.seed.trim() ? Number(scene.seed) : null;
    if (seed != null && (!Number.isInteger(seed) || seed < 0 || seed > 4294967295)) { setGenerationError(t('invalidSeed')); return; }
    if (scene.text.length > 3000) { setGenerationError(t('tooLong')); return; }
    setSubmitting(true); setGenerationError(null); setNotice(null);
    try { await projects.flush(); const saved=projects.getSnapshot(); if(!saved.id || saved.status!=='saved')throw new Error(t('projectActionFailed')); await backend.submit({ projectId: saved.id, sceneId: scene.id, title: scene.title.trim() || t('newScene'), text: scene.text, voiceId: voiceMode === 'clone' ? selectedVoiceId : null, modelId: synthesisModel?.id, presetVoice: synthesisModel?.presetVoices?.includes(scene.presetVoice ?? '') ? scene.presetVoice : synthesisModel?.presetVoices?.[0], voiceDescription: designDescription, voiceMode: backend.health?.supportsVoiceModes ? voiceMode : undefined, emotion: deliveryEmotion, language: effectiveLanguage, seed }); }
    catch (error) { setGenerationError(error instanceof Error ? error.message : t('generationFailed')); }
    finally { setSubmitting(false); }
  };
  const jobStage = (stage: string) => ({ queued: t('jobQueued'), starting: t('jobStarting'), loading: t('jobLoading'), reference: t('jobReference'), generating: t('jobGenerating'), saving: t('jobSaving') }[stage] ?? t('jobStarting'));
  const latestSceneJob = backend.jobs.filter(j => j.request.projectId === projects.id && j.request.sceneId === scene?.id).sort((a,b) => a.createdAt.localeCompare(b.createdAt)).at(-1);
  const latestFailure = latestSceneJob?.status === 'failed' ? latestSceneJob : undefined;

  const timelineItems=assemblyItems.map(item=>{const span=montage.result?.spans.find(s=>s.sceneId===item.scene.id);return span?{...item,start:span.start,end:span.end,duration:span.end-span.start}:item;});
  const totalDuration=montage.result?.duration??assemblyItems.filter(i=>!i.excluded && i.recording).at(-1)?.end??0;
  const recordingProgress = (index: number | null) => index != null && playingIndex === index && !montage.active ? Math.min(1, elapsed / recordings[index].duration) : 0;
  const sceneProgress = (index:number)=>{const item=timelineItems[index];if(!item?.recording || !item.edit || item.excluded)return 0;if(montage.active)return Math.max(0,Math.min(1,(montage.elapsed-item.start)/item.duration));return Math.max(0,Math.min(1,((playingIndex===audioIndexFor(item.scene)?elapsed:0)-item.edit.start)/item.duration));};

  useEffect(() => {
    if (!playing) return;
    let frame: number;
    const sync = () => { if (!pendingSeek.current) setElapsed(audio.current?.currentTime ?? 0); frame = requestAnimationFrame(sync); };
    frame = requestAnimationFrame(sync);
    return () => cancelAnimationFrame(frame);
  }, [playing]);

  useEffect(() => {
    const media = matchMedia('(prefers-color-scheme: dark)');
    const apply = () => { document.documentElement.dataset.mode = theme === 'system' ? (media.matches ? 'dark' : 'light') : theme; };
    apply(); media.addEventListener('change', apply); return () => media.removeEventListener('change', apply);
  }, [theme]);
  useEffect(() => { document.documentElement.lang = locale; document.title = `${project.title || 'Voice Studio'} — Voice Studio`; }, [locale, project.title]);
  useEffect(() => {
    try { localStorage.setItem('vs.locale',JSON.stringify(locale));localStorage.setItem('vs.theme',JSON.stringify(theme)); }
    catch { /* Interface preferences do not affect server project persistence. */ }
  },[locale,theme]);
  useEffect(() => { const pop = () => {setView(readView());setAssemblyMode(new URLSearchParams(location.search).get('mode')==='assembly');setSelected(new URLSearchParams(location.search).get('scene')??'');}; addEventListener('popstate', pop); return () => removeEventListener('popstate', pop); }, []);
  const navigate = (next: View) => { setView(next); setNotice(null); const url = new URL(location.href); for (const key of ['q','task','status','language','feature','integration']) url.searchParams.delete(key); next === 'studio' ? url.searchParams.delete('view') : url.searchParams.set('view', next); history.pushState({}, '', url); requestAnimationFrame(() => scrollTo({ top: 0, behavior: 'instant' })); };
  useEffect(()=>{const nav=headerRef.current?.querySelector('nav'),active=nav?.querySelector('.nav-active');if(!nav || !active)return;const bounds=nav.getBoundingClientRect(),button=active.getBoundingClientRect();if(button.right>bounds.right)nav.scrollLeft+=button.right-bounds.right;else if(button.left<bounds.left)nav.scrollLeft+=button.left-bounds.left;},[view,locale]);
  useEffect(()=>{const ids=cleanups.tasks.filter(v=>v.job.status==='succeeded').map(v=>v.task.id);if(ids.length)void backend.ensureRecordings(ids);},[cleanups.tasks,backend.ensureRecordings]);
  const openSceneCleanup=()=>{if(!scene || !recording || !projects.id)return;pauseAllPlayback();const existing=cleanups.tasks.find(v=>v.task.id===recording.id && v.task.projectId===projects.id && v.task.sceneId===scene.id);if(existing || recording.modelId==='resemble-enhance'){cleanups.show(recording.id);navigate('cleanup');return;}cleanups.open({kind:'scene',projectId:projects.id,sceneId:scene.id,sourceId:recording.id,title:scene.title,url:recording.url});navigate('cleanup');};
  const openFinalCleanup=()=>{if(!projects.id)return;pauseAllPlayback();cleanups.open({kind:'final',projectId:projects.id,title:project.title});navigate('cleanup');};
  const startCleanupSource=async()=>{const pending=cleanups.pending;if(!pending)return;await projects.flush();const saved=projects.getSnapshot();if(saved.status!=='saved' || saved.id!==pending.projectId)throw new Error(locale==='ru'?'Откройте исходный проект и повторите очистку.':'Open the source project and try again.');if(pending.kind==='scene')await cleanups.source({projectId:pending.projectId,sceneId:pending.sceneId,sourceId:pending.sourceId},'scene');else{const master=await montage.prepare();await cleanups.source({projectId:pending.projectId,assemblyId:master.id},'final');}};
  const openCleanupSource=async(view:CleanupView)=>{if(!view.task.projectId)return;await projects.open(view.task.projectId);if(view.task.sceneId)chooseScene(view.task.sceneId);setAssembly(true);navigate('studio');};
  const applyCleanup=async(view:CleanupView)=>{await projects.flush();const saved=projects.getSnapshot();if(saved.id!==view.task.projectId || saved.status!=='saved')throw new Error(locale==='ru'?'Сначала откройте исходный проект кнопкой «К сцене».':'Open the source project with “Open scene” first.');await cleanups.apply(view.task.id,saved.revision);await projects.refresh();await backend.ensureRecordings([view.task.id]);await cleanups.refresh();chooseScene(view.task.sceneId!);setAssembly(true);navigate('studio');};
  const updateScene = (patch: Partial<Scene>) => { if (scene) setProject(p => ({ ...p, scenes: p.scenes.map(s => s.id === scene.id ? { ...s, ...patch } : s) })); };
  const chooseScene = (id: string) => { setSelected(id);setNotice(null);const url=new URL(location.href);url.searchParams.set('scene',id);history.replaceState(null,'',url); };
  const selectionProject=useRef(projects.id);
  useEffect(()=>{
    if(!projects.ready||projects.switching)return;
    const url=new URL(location.href);
    const next=resolveSceneSelection(project.scenes,selected,url.searchParams.get('scene'),selectionProject.current!==projects.id);
    selectionProject.current=projects.id;
    if(next!==selected)setSelected(next);
    if(next)url.searchParams.set('scene',next);else url.searchParams.delete('scene');
    if(url.href!==location.href)history.replaceState(null,'',url);
  },[projects.ready,projects.switching,projects.id,project.scenes,selected]);
  const addScene = () => {
    const next: Scene = { id: crypto.randomUUID(), title: t('newScene'), text: '', speechLanguage: 'ru', emotion: 'calm', temperature: 0.7, seed: '', audioIndex: null, voiceId: selectedVoiceId || undefined };
    setProject(p => ({ ...p, scenes: [...p.scenes, next] })); setSelected(next.id); setNotice(null);
  };
  const duplicate = (source: Scene) => { const next = { ...source, id: crypto.randomUUID(), title: `${source.title} (2)` }; setProject(p => ({ ...p, scenes: [...p.scenes, next] })); setSelected(next.id); };
  const remove = (source: Scene) => {
    const index = project.scenes.findIndex(s => s.id === source.id); setDeleted({ scene: source, index });
    setProject(p => ({ ...p, scenes: p.scenes.filter(s => s.id !== source.id) }));
    if (selected === source.id) setSelected(project.scenes[index + 1]?.id ?? project.scenes[index - 1]?.id ?? '');
  };
  const undo = () => { if (!deleted) return; setProject(p => { const scenes = [...p.scenes]; scenes.splice(deleted.index, 0, deleted.scene); return { ...p, scenes }; }); setSelected(deleted.scene.id); setDeleted(null); };
  const applyMarkup = (edit: SpeechEdit) => {
    updateScene({ text: edit.text });
    requestAnimationFrame(() => { editor.current?.focus(); editor.current?.setSelectionRange(edit.caret, edit.caret); });
  };
  const insert = (text: string) => { if(scene) applyMarkup(insertSpeechTag(scene.text,editor.current?.selectionStart ?? scene.text.length,text)); };
  const insertPause = () => { if(scene) applyMarkup(insertSpeechPause(scene.text,editor.current?.selectionEnd ?? scene.text.length,synthesisModel?.markup)); };
  const playRecording = async (index:number,restart=false)=>{
    const el=audio.current;if(!el)return;
    if(!restart && playing && playingIndex===index && !montage.active){el.pause();return;}
    montage.deactivate();pauseAllPlayback(el);
    if(restart || playingIndex!==index || el.ended){pendingSeek.current=null;el.src=recordings[index].url;setElapsed(0);}
    setMiniDismissed(false);setPlayingIndex(index);setNotice(null);
    try{await el.play();}catch{setNotice('playbackError');setPlaying(false);}
  };
  const seekRecording=(index:number,seconds:number)=>{
    const el=audio.current;if(!el || !Number.isFinite(seconds))return;
    const target=Math.max(0,Math.min(recordings[index].duration,seconds));
    const resume=!el.paused && !el.ended;
    const url=recordings[index].url;
    montage.deactivate();pauseAllPlayback(el);
    setMiniDismissed(false);setPlayingIndex(index);setElapsed(target);setNotice(null);
    if (el.getAttribute('src') !== url || el.readyState === 0) {
      pendingSeek.current = { url, seconds: target };
      el.src = url;
      el.load();
    } else { pendingSeek.current = null; el.currentTime = target; }
    if (resume) void el.play().catch(error => {
      if (error instanceof DOMException && error.name === 'AbortError') return;
      setNotice('playbackError'); setPlaying(false);
    });
  };
  const applyPendingSeek = () => {
    const el = audio.current, pending = pendingSeek.current;
    if (!el || !pending || el.getAttribute('src') !== pending.url) return;
    pendingSeek.current = null;
    el.currentTime = pending.seconds;
    setElapsed(pending.seconds);
  };
  const finish=()=>{setPlaying(false);setElapsed(playingIndex==null?0:recordings[playingIndex].duration);};
  const exportProject = () => {
    const blob = new Blob([JSON.stringify({ schemaVersion: 2, ...project }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'voice-studio-project.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const modeIcon = theme === 'light' ? Sun : theme === 'system' ? Desktop : Moon;
  const playIcon = (index: number) => playing && playingIndex === index ? <Pause size={18} weight="fill" /> : <Play size={18} weight="fill" />;

  const deliveryControl = <div className="setting-section"><label htmlFor="delivery">{t('delivery')}</label><Select id="delivery" label={t('delivery')} disabled={!scene} value={deliveryEmotion} onChange={value => updateScene({ emotion: value as Emotion })} options={availableEmotions.map(emotion => ({ value: emotion, label: t(deliveryLabel(synthesisModel?.id,emotion)) }))} />{fishModel && <button disabled={!scene} className="text-link" onClick={() => insert(`${tags[scene.emotion]} `)}>{t('addEmotion')}</button>}</div>;
  return <>
    <a className="skip" href="#main">{t('skip')}</a>
    <header ref={headerRef} className="app-header"><div className="header-inner">
      <a className="brand" href="/" onClick={e => { e.preventDefault(); navigate('studio'); }}><Waveform size={28} weight="bold" /><span>Voice Studio</span></a>
      <nav aria-label={locale === 'ru' ? 'Главная навигация' : 'Main navigation'}>
        {(['studio','projects','voices','models','library','cleanup'] as View[]).map(v => <button key={v} className={view === v ? 'nav-active' : ''} aria-current={view === v ? 'page' : undefined} onClick={() => navigate(v)}>{t(v)}</button>)}
      </nav>
      <div className="preferences">
        <Menu label={locale === 'ru' ? 'Русский' : 'English'} icon={Globe} className="locale-menu">
          <p className="menu-label">{t('interfaceLanguage')}</p>
          {(['ru','en'] as Locale[]).map(l => <button key={l} onClick={() => setLocale(l)} aria-pressed={locale === l}><span>{l === 'ru' ? 'Русский' : 'English'}</span>{locale === l && <Check size={16} />}</button>)}
        </Menu>
        <Menu label={t(theme)} icon={modeIcon} className="theme-menu">
          {([['light',Sun],['dark',Moon],['system',Desktop]] as [Theme, Icon][]).map(([m,Glyph]) => <button key={m} onClick={() => setTheme(m)} aria-pressed={theme === m}><Glyph size={20} /><span>{t(m)}</span>{theme === m && <Check size={16} className="accent" />}</button>)}
        </Menu>
      </div>
    </div></header>

    {(view === 'studio') ? <main id="main" className="studio-shell">
      <div className="project-heading"><div className="project-name"><input aria-label={t('projectTitle')} maxLength={200} disabled={!projects.ready || projects.switching} value={project.title} onChange={e => setProject(p => ({ ...p, title: e.target.value }))} /><span className={['offline','error','conflict'].includes(projects.status)?'storage-error':'saved'} role="status">{t(projects.status==='loading'?'projectLoading':projects.status==='saving'?'projectSaving':projects.status==='saved'?'projectSaved':projects.status==='conflict'?'projectConflict':projects.status==='offline' && !projects.cacheOk?'projectMemoryOnly':'projectOffline')}</span></div>
        <div className="project-actions"><button type="button" className="quiet assembly-mode-toggle" aria-pressed={assemblyMode} onClick={()=>setAssembly(!assemblyMode)}><Scissors size={18}/>{locale==='ru'?(assemblyMode?'К тексту':'Монтаж'):(assemblyMode?'Edit script':'Montage')}</button>
        <Menu label={t('export')} icon={Export} className="export-menu"><button type="button" disabled={!assemblyReady || montage.busy} onClick={()=>void montage.download('wav')}><DownloadSimple size={18}/>{locale==='ru'?'Итоговая запись / WAV':'Final recording / WAV'}</button><button type="button" disabled={!assemblyReady || montage.busy} onClick={()=>void montage.download('mp3')}><DownloadSimple size={18}/>{locale==='ru'?'Итоговая запись / MP3':'Final recording / MP3'}</button><button onClick={exportProject}><DownloadSimple size={18} />{t('exportProject')}</button>{recording && <a href={recording.url} download><DownloadSimple size={18} />{t('downloadAudio')}</a>}<p className="menu-help">{t('exportHelp')}</p></Menu></div>
      </div>
      {['offline','conflict','error'].includes(projects.status) && <div className="project-sync-notice" role="status"><p>{t(projects.status==='conflict'?'projectConflictHelp':'projectOfflineHelp')}{projects.error && <span>{projects.error}</span>}</p><div>{projects.status==='conflict'?<><button type="button" className="quiet" disabled={projects.switching} onClick={()=>void projects.saveCopy().catch(error=>setGenerationError(String(error)))}>{t('saveProjectCopy')}</button><button type="button" className="quiet" disabled={projects.switching} onClick={()=>void projects.loadServer().catch(error=>setGenerationError(String(error)))}>{t('loadServerProject')}</button></>:<button type="button" className="quiet" onClick={()=>void projects.retry()}>{t('retryProjectSave')}</button>}</div></div>}
      {assemblyMode?<AssemblyPanel project={project} setProject={setProject} projectId={projects.id} recordings={recordings} selected={selected} choose={chooseScene} locale={locale} montage={montage} pausePlayback={el=>{montage.deactivate();pauseAllPlayback(el);}} openText={()=>setAssembly(false)} cleanScene={openSceneCleanup} cleanFinal={openFinalCleanup}/>:<div className="workspace" inert={!projects.ready || projects.switching}>
        <aside className="scene-panel panel" aria-label={t('scenes')}>
          <div className="scene-heading"><h2>{t('scenes')}</h2><button className="quiet add-scene" aria-label={t('addScene')} title={t('addScene')} onClick={addScene}><Plus size={20} /><span>{t('addScene')}</span></button></div>
          <div className="scene-list">{project.scenes.map((s, i) => <div className={`scene-item ${scene?.id === s.id ? 'is-selected' : ''}`} key={s.id}>
            <button className="scene-select" aria-pressed={scene?.id === s.id} onClick={() => chooseScene(s.id)}><span className="scene-number">{String(i + 1).padStart(2, '0')}</span><span className="scene-label"><span>{s.title || t('newScene')}</span><small title={sceneVoiceLabel(s)}>{sceneVoiceLabel(s)}</small></span></button>
            <Menu label={t('sceneMenu')} icon={DotsThree} className="scene-actions"><button onClick={() => duplicate(s)}>{t('duplicate')}</button><button onClick={() => remove(s)}>{t('remove')}</button></Menu>
          </div>)}{!project.scenes.length && <p className="empty-copy">{t('emptyScenes')}</p>}</div>
          <div className="scene-panel-foot"><FolderOpen size={16} /><span>{t('currentProject')}</span></div>
        </aside>

        <section className="editor-panel panel" aria-label={t('text')}>
          {scene ? <>
            <div className="editor-header"><div className="editor-title-row"><input maxLength={200} aria-label={t('sceneTitle')} value={scene.title} onChange={e => updateScene({ title: e.target.value })} /><Menu label={locale==='ru'?'Действия с дублем':'Take actions'} icon={DotsThree} className="take-actions-menu"><button type="button" disabled={!recording || !projects.ready || projects.switching} onClick={openSceneCleanup}>{locale==='ru'?'Улучшить выбранный дубль':'Enhance selected take'}</button></Menu></div>
              <div className="editor-tabs" role="group" aria-label={t('text')}><button aria-pressed={tab === 'text'} className={tab === 'text' ? 'selected' : ''} onClick={() => setTab('text')}>{t('text')}</button><button aria-pressed={tab === 'markup'} className={tab === 'markup' ? 'selected' : ''} onClick={() => setTab('markup')}>{t('markup')}</button></div>
            </div>
            <div className="editor-body">
              {tab === 'markup' && <p className="markup-help">{t(fishModel ? 'markupHelp' : synthesisModel?.markup==='dia' ? 'dialogueMarkupHelp' : synthesisModel?.markup==='ssml' ? 'ssmlHelp' : synthesisModel?.markup==='chatterbox' ? 'chatterboxMarkupHelp' : synthesisModel?.markup==='orpheus' ? 'orpheusMarkupHelp' : 'generalMarkupHelp')}</p>}
              <textarea ref={editor} maxLength={3000} className={tab === 'markup' ? 'script-editor markup-editor' : 'script-editor'} aria-label={t('text')} value={scene.text} onChange={e => { updateScene({ text: e.target.value }); setNotice(null); }} placeholder={t('placeholder')} spellCheck={false} />
              <div className="editor-tools">{fishModel && <button className="tag-button" onClick={() => insert(`${tags[scene.emotion]} `)}><SlidersHorizontal size={14} />{t('emphasis')}</button>}<button className="pause-tag" onClick={insertPause} aria-label={t('pause')} data-tooltip={t('pauseHelp')}>{t('pause')}</button><span>{scene.text.length} {t('chars')}</span></div>
            </div>
            <div className="takes">
              {recording?<div className={`take-row ${recording ? 'take-selected' : ''}`}><button className="take-play" disabled={!recording} aria-label={`${playing && playingIndex === sceneAudioIndex ? t('pausePlayback') : t('play')} ${t('selectedTake')}`} onClick={() => sceneAudioIndex != null && void playRecording(sceneAudioIndex)}>{sceneAudioIndex != null ? playIcon(sceneAudioIndex) : <Play size={18} weight="fill" />}</button><span>{recording?.generated ? t('selectedTake') : t('sampleAudio')}</span>{recording && <SeekWave peaks={recording.peaks} progress={recordingProgress(sceneAudioIndex)} duration={recording.duration} label={`${t('seek')} — ${t('selectedTake')}`} onSeek={seconds => sceneAudioIndex != null && seekRecording(sceneAudioIndex, seconds)} />}<small>{recording ? time(recording.duration) : t(backend.connecting && scene.selectedTakeId ? 'loadingAudio' : 'noAudio')}</small></div>:<p className="empty-take" role="status">{t(backend.connecting && scene.selectedTakeId?'loadingAudio':'noAudio')}</p>}
              {sceneTakes.length > 0 && <div className="take-picker">{sceneTakes.map((r,i) => <button key={r.id} aria-pressed={sceneAudioIndex === r.index} onClick={() => updateScene({ selectedTakeId: r.generated?r.id:undefined })}>{r.generated?`${t('take')} ${i+1}`:locale==='ru'?'Исходная запись':'Original recording'} <small>{time(r.duration)}</small></button>)}</div>}
              {recording?.generated && <details className="take-source"><summary>{t('takeText')}</summary><p>{recording.sourceText}</p><small>{t('model')}: {modelCatalog.catalog?.models.find(model => model.id === recording.modelId)?.name ?? 'Fish S2 Pro'} / {t('sceneVoice')}: {recordingVoiceName(recording)}{!recording.modelId?.startsWith('piper-') && <> / {t('delivery')}: {t(deliveryLabel(recording.modelId,recording.emotion ?? 'calm'))}{recording.temperature!=null && <> / {t('temperature')}: {recording.temperature}</>} / Seed: {recording.seed}</>}</small></details>}
              
            </div>
          </> : <div className="empty-editor"><Waveform size={40} /><h2>{t('emptyScenes')}</h2><button className="primary" onClick={addScene}><Plus size={20} />{t('addScene')}</button></div>}
        </section>

        <aside className={`inspector panel ${voiceModes?.length ? 'multiple-voice-modes' : ''}`} data-expanded={inspectorExpanded} aria-label={t('sceneVoice')}>
          <button type="button" className="inspector-toggle" aria-expanded={inspectorExpanded} aria-controls="voice-settings" onClick={()=>setInspectorExpanded(!inspectorExpanded)}><span><strong>{t('voiceSettings')}</strong><small>{voiceMode==='clone'?voiceName(selectedVoiceId):synthesisModel?.name??t('chooseInstalledModel')}</small></span>{inspectorExpanded?<CaretUp size={18}/>:<CaretDown size={18}/>}</button>
          <div id="voice-settings" className="inspector-scroll"><h2>{t('sceneVoice')}</h2>
            <div className="setting-section"><div className="setting-label-row"><label htmlFor="model">{t('model')}</label><button className="text-link" onClick={() => navigate('models')}>{t('manageModels')}</button></div><Select id="model" label={t('model')} disabled={!installedSynthesis.length || !!modelCatalog.busy || submitting} value={synthesisModel?.id ?? ''} onChange={value => { void modelCatalog.action(value,'select').catch(error => setGenerationError(error instanceof Error ? error.message : t('modelChangeFailed'))); }} options={installedSynthesis.length ? installedSynthesis.map(model => ({value:model.id,label:model.name,description:model.format})) : [{value:'',label:t(synthesisLoading?'modelsLoading':'chooseInstalledModel')}]} /></div>
            {!!voiceModes && voiceModes.length>1 && <div className="setting-section"><Select id="voice-mode" label={t('voiceMode')} value={voiceMode} onChange={value=>updateScene({voiceMode:value as Scene['voiceMode'],...(value==='design' && controlledVoice?{voiceDescription:designDescription}:{})})} options={voiceModes.map(value=>({value,label:value==='clone'?t('cloneVoice'):designLabel}))}/></div>}
            {voiceMode === 'clone' && <div className="voice-row"><span className="avatar">{voiceName(selectedVoiceId).slice(0,1).toUpperCase()}</span><Select label={t('sceneVoice')} disabled={!scene || !backend.voices.length} value={selectedVoiceId} onChange={value => { referenceAudio.current?.pause(); updateScene({ voiceId: value }); }} options={[...(!selectedVoice ? [{ value: selectedVoiceId, label: t('chooseVoice') }] : []), ...backend.voices.map(v => ({ value: v.id, label: v.name }))]} /><button className="round quiet" disabled={!selectedVoice} aria-label={t('previewVoice')} onClick={() => void previewSelectedVoice()}>{previewingVoice ? <Pause size={18} weight="fill" /> : <Play size={18} weight="fill" />}</button></div>}
            {voiceMode === 'clone' && synthesisModel?.referenceLanguages && <p className="setting-help">{t('referenceLanguageHelp')}: {synthesisModel.referenceLanguages.map(value=>new Intl.DisplayNames([locale],{type:'language'}).of(value) ?? value).join(', ')}.</p>}
            {voiceMode === 'preset' && <div className="setting-section"><label htmlFor="preset-voice">{t('readyVoice')}</label><Select id="preset-voice" label={t('readyVoice')} value={synthesisModel?.presetVoices?.includes(scene?.presetVoice ?? '') ? scene?.presetVoice ?? '' : synthesisModel?.presetVoices?.[0] ?? ''} onChange={presetVoice => updateScene({presetVoice})} options={(synthesisModel?.presetVoices ?? []).map(value=>({value,label:value}))} /><p className="setting-help">{t('presetVoiceHelp')}</p></div>}
            {voiceMode === 'design' && controlledVoice && <div className="setting-section"><div className="spark-voice-controls">
              <div><label htmlFor="spark-gender">{t('voiceType')}</label><Select id="spark-gender" label={t('voiceType')} value={sparkSettings.gender} onChange={gender=>updateScene({voiceDescription:sparkDescription({...sparkSettings,gender:gender as 'male'|'female'})})} options={(['male','female'] as const).map(value=>({value,label:t(value==='male'?'maleVoice':'femaleVoice')}))}/></div>
              {(['pitch','speed'] as const).map(key=><div key={key}><label htmlFor={`spark-${key}`}>{t(key==='pitch'?'voicePitch':'voicePace')}</label><Select id={`spark-${key}`} label={t(key==='pitch'?'voicePitch':'voicePace')} value={sparkSettings[key]} onChange={value=>updateScene({voiceDescription:sparkDescription({...sparkSettings,[key]:value as SparkLevel})})} options={sparkLevels.map(value=>({value,label:t(`spark_${key}_${value}`)}))}/></div>)}
            </div><p className="setting-help">{t('controlledVoiceHelp')}</p></div>}
            {voiceMode === 'design' && !controlledVoice && <div className="setting-section"><label htmlFor="voice-description">{t('voiceDescription')}</label><textarea id="voice-description" className="voice-description" maxLength={1000} rows={voiceModes?.length?2:4} value={scene?.voiceDescription ?? ''} placeholder={synthesisModel?.voiceDescriptionExample ?? t('voiceDescriptionPlaceholder')} onChange={event => updateScene({voiceDescription:event.target.value,...(backend.health?.supportsVoiceModes?{voiceMode:'design' as const}:{})})} /><p className="setting-help">{synthesisModel?.voiceDescriptionHelp?.[locale] ?? t(voiceModes?.length?'voiceDesignHelpShort':'voiceDesignHelp')}</p></div>}
            <div className="setting-section language-setting">{fixedSpeechLanguage?<div className="fixed-setting" title={textLanguage?t('modelLanguageDetected'):undefined}><span>{t('speechLanguage')}</span><span id="speech-language">{effectiveLanguage==='auto'?t('auto'):new Intl.DisplayNames([locale],{type:'language'}).of(effectiveLanguage)??effectiveLanguage}</span></div>:<><label htmlFor="speech-language">{t('speechLanguage')}</label><Select id="speech-language" label={t('speechLanguage')} disabled={!scene} value={effectiveLanguage} onChange={value=>updateScene({speechLanguage:value})} options={[...(synthesisModel?.autoLanguage===false?[]:[{value:'auto',label:t('auto')}]),...(synthesisModel?.languages ?? ['ru','en']).map(value=>({value,label:new Intl.DisplayNames([locale],{type:'language'}).of(value) ?? value}))]} /></>}</div>
            {canDirectEmotion && !compactEmotion && deliveryControl}
            {synthesisModel?.supportsSeed !== false && <div className="advanced"><button className="advanced-trigger" aria-expanded={advanced} onClick={() => setAdvanced(!advanced)}><span>{t('advanced')}</span>{advanced ? <CaretDown size={16} /> : <CaretRight size={16} />}</button>{advanced && <div className="advanced-body">{canDirectEmotion && compactEmotion && deliveryControl}<label htmlFor="seed">{t('seed')}</label><input id="seed" type="number" min="0" max="4294967295" step="1" value={scene?.seed ?? ''} placeholder={t('random')} onChange={e => updateScene({ seed: e.target.value })} /><p>{t(fishModel ? 'emotionHelp' : 'generalMarkupHelp')}</p>{synthesisModel?.defaultTemperature===0.8 && <p>{t('fixedTemperature')}</p>}</div>}</div>}
          </div>
          <div className="generation-area">{notice && <div className="notice" role="status"><Info size={17} /><p>{t(notice)}</p><button aria-label={t('close')} onClick={() => setNotice(null)}><X size={15} /></button></div>}{(!backend.health || !voiceReady || !synthesisReady) && <p className="engine-status">{t(backend.connecting ? 'engineConnecting' : !backend.health ? 'engineOffline' : synthesisLoading ? 'modelsLoading' : modelCatalog.error ? 'modelsUnavailable' : !synthesisReady ? 'installSynthesis' : voiceMode === 'design' ? 'describeVoiceFirst' : 'voiceMissing')}{backend.health && !synthesisReady && <button className="text-link" onClick={() => navigate('models')}>{t('openModels')}</button>}</p>}{sceneJob && <div className="job-progress" role="status"><strong>{jobStage(sceneJob.stage)}</strong>{sceneJob.total > 0 && <span>{sceneJob.part} / {sceneJob.total}</span>}</div>}{(generationError || latestFailure?.error) && <p className="generation-error" role="alert">{generationError || latestFailure?.error}</p>}<button className="primary generate-button" disabled={!projects.ready || projects.switching || projects.status==='conflict' || !scene || !backend.health || !voiceReady || !synthesisReady || submitting || !!modelCatalog.busy || !!sceneJob} aria-busy={submitting || !!sceneJob} onClick={() => void generate()}><Waveform size={22} />{t(submitting || sceneJob ? 'generating' : 'generate')}</button></div>
        </aside>
      </div>}
    </main> : <main id="main" className="secondary-shell">
      <div className="secondary-heading"><h1>{t(view)}</h1><p>{t(view === 'projects' ? 'projectsHelp' : view === 'voices' ? 'voicesHelp' : view === 'models' ? 'modelsHelp' : view==='cleanup'?'cleanupHelp':'libraryHelp')}</p></div>
      {view === 'cleanup' && <CleanupPanel cleanup={cleanups} models={modelCatalog} locale={locale} startSource={startCleanupSource} apply={applyCleanup} openSource={openCleanupSource} openModels={()=>navigate('models')} pausePlayback={pauseAllPlayback}/>}
      {view === 'projects' && <ProjectsPanel projects={projects} locale={locale} openStudio={()=>navigate('studio')} exportProject={exportProject}/>}
      {view === 'voices' && <VoicesPanel supportsReferenceLanguages={backend.health?.supportsReferenceLanguages} transcriptionLanguages={transcriptionModel?.languages??[]} transcriptionReady={transcriptionReady} openModels={() => navigate('models')} locale={locale} voices={backend.voices} online={!!backend.health} connecting={backend.connecting} refreshVoices={backend.refreshVoices} deleteVoice={backend.deleteVoice} blockedVoiceIds={backend.jobs.filter(job=>['queued','running'].includes(job.status)).flatMap(job=>job.request.voiceId?[job.request.voiceId]:[])} useVoice={id => { if (scene) updateScene({ voiceId: id }); else { const next: Scene = { id: crypto.randomUUID(), title: t('newScene'), text: '', speechLanguage: 'auto', emotion: 'calm', temperature: 0.8, seed: '', audioIndex: null, voiceId: id }; setProject(p => ({ ...p, scenes: [...p.scenes, next] })); setSelected(next.id); } pauseAllPlayback(); navigate('studio'); }} pausePlayback={pauseAllPlayback} />}
      {view === 'models' && <ModelsPanel locale={locale} models={modelCatalog} backend={backend} workbench={workbench} openCleanup={()=>navigate('cleanup')} />}
      {view === 'library' && <LibraryPanel recordings={recordings} locale={locale} playingIndex={playingIndex} playing={playing} onPlay={index=>void playRecording(index)} onSeek={(index,seconds)=>seekRecording(index,seconds)} progress={index=>recordingProgress(index)} voiceName={recordingVoiceName} registerRecordings={backend.registerRecordings} historyVersion={backend.jobs.reduce((latest,job)=>job.status==='succeeded' && (job.completedAt??'')>latest?job.completedAt!:latest,'')}/>}
      {notice && view !== 'models' && <p className="inline-notice" role="status">{t(notice)}</p>}
    </main>}

    {(view==='studio' || (montage.active || playingIndex!==null) && !miniDismissed) && <footer ref={dockRef} className={`playback-dock ${view==='studio'?'timeline-footer':'mini-player'}`} data-expanded={view==='studio' && timelineOpen} aria-label={t(view==='studio'?'timeline':'nowPlaying')}><div className="timeline-inner">
      <div className="transport"><button type="button" className="transport-play" disabled={montage.busy || (!assemblyReady && (playingIndex===null || montage.active))} aria-label={montage.active?montage.playing?t('pausePlayback'):t('playProject'):playing?t('pausePlayback'):view==='studio'?t('playProject'):t('play')} onClick={()=>{if(montage.active){if(montage.playing)montage.pause();else void montage.preview();}else if(playing)audio.current?.pause();else if(view!=='studio' && playingIndex!==null)void playRecording(playingIndex);else {setMiniDismissed(false);void montage.preview(0);}}}>{(montage.active?montage.playing:playing)?<Pause size={22} weight="fill"/>:<Play size={22} weight="fill"/>}</button><span className="transport-time">{time(montage.active?montage.elapsed:elapsed)} / {time(montage.active?montage.result?.duration??totalDuration:playingIndex==null?totalDuration:recordings[playingIndex].duration)}</span><VolumeControl locale={locale} label={t('timeline')}/></div>
      {view==='studio'?<><div className="timeline" id="project-timeline" hidden={!timelineOpen} aria-label={t('timeline')}><ProjectTimeline items={timelineItems} locale={locale} selected={scene?.id} elapsed={montage.elapsed} active={montage.active} disabled={!assemblyReady || montage.busy} progress={sceneProgress} choose={chooseScene} seek={seconds=>{setMiniDismissed(false);void montage.seek(seconds);}}/></div><button type="button" className="quiet dock-toggle" aria-controls="project-timeline" aria-expanded={timelineOpen} disabled={shortViewport} aria-label={t(shortViewport?'timelineSmallScreen':timelineOpen?'collapseTimeline':'expandTimeline')} title={t(shortViewport?'timelineSmallScreen':timelineOpen?'collapseTimeline':'expandTimeline')} onClick={()=>setTimelineExpanded(!timelineExpanded)}><span>{t('timelineShort')}</span>{timelineOpen?<CaretDown size={18}/>:<CaretUp size={18}/>}</button></>:<><div className="mini-recording"><strong>{montage.active?project.title:playingIndex===null?'':recordings[playingIndex].title}</strong><span>{montage.active?(locale==='ru'?'Итоговая запись':'Final recording'):playingIndex===null?'':recordingVoiceName(recordings[playingIndex])}</span></div><div className="mini-seek">{montage.active && montage.result?<SeekWave peaks={montage.result.peaks} progress={montage.elapsed/montage.result.duration} duration={montage.result.duration} label={t('seek')} onSeek={seconds=>void montage.seek(seconds)}/>:playingIndex!==null && <SeekWave peaks={recordings[playingIndex].peaks} progress={recordingProgress(playingIndex)} duration={recordings[playingIndex].duration} label={t('seek')} onSeek={seconds=>seekRecording(playingIndex,seconds)}/>}</div><button type="button" className="quiet icon-button" aria-label={t('closePlayer')} onClick={()=>{montage.pause();audio.current?.pause();setMiniDismissed(true);}}><X size={18}/></button></>}
      {(montage.error || montage.busy) && !assemblyMode && <p className="dock-assembly-status" role={montage.error?'alert':'status'}>{montage.error || (locale==='ru'?'Собираем итоговую запись…':'Assembling final audio…')}</p>}
    </div></footer>}
    <audio {...montage.audioProps} aria-hidden="true"/>
    {deleted && <div className="undo-notice" role="status"><span>{t('removed')}</span><button className="text-link" onClick={undo}><ArrowCounterClockwise size={16} />{t('undo')}</button><button className="icon-button" aria-label={t('close')} onClick={() => setDeleted(null)}><X size={16} /></button></div>}
    <audio ref={referenceAudio} onPlay={() => setPreviewingVoice(true)} onPause={() => setPreviewingVoice(false)} onEnded={() => setPreviewingVoice(false)} onError={() => { setPreviewingVoice(false); setNotice('playbackError'); }} />
    <audio ref={audio} onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onEnded={finish} onLoadedMetadata={applyPendingSeek} onTimeUpdate={() => { if (!pendingSeek.current) setElapsed(audio.current?.currentTime ?? 0); }} onError={() => { pendingSeek.current = null; setPlaying(false); setNotice('playbackError'); }} />
  </>;
}
