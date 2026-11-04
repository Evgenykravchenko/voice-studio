import {useEffect,useRef,useState,useId,type Dispatch,type SetStateAction,type PointerEvent} from 'react';
import {Scissors,ArrowCounterClockwise,ArrowClockwise,Play,DownloadSimple,DotsThree} from '@phosphor-icons/react';
import type {Project,Recording,Scene,Locale,ClipEdit} from './types';
import {arrangement,audioSnapshot,restoreAudio,setClipEdit,sourceId} from './assembly-utils';
import {Wave} from './Wave';
import {AudioPlayer} from './AudioPlayer';
import {Select} from './Select';
import type {useAssembly} from './useAssembly';
import {audioTime} from './audio-utils';
import {SceneOrderList} from './SceneOrderList';
import {SceneGain} from './SceneGain';
import {Menu} from './Menu';
function NumberField({label,value,min,max,step=.01,onCommit,disabled=false,hint}:{hint?:string;label:string;value:number;min:number;max:number;step?:number;onCommit:(value:number)=>void;disabled?:boolean}){
  const helpId=useId();
  const [draft,setDraft]=useState(String(value));useEffect(()=>setDraft(String(Math.round(value*1000)/1000)),[value]);
  const commit=()=>{const next=Number(draft.replace(',','.'));if(draft.trim() && Number.isFinite(next)){const v=Math.round(Math.max(min,Math.min(max,next))*1000)/1000;if(v!==value)onCommit(v);setDraft(String(v));}else setDraft(String(value));};
  return <label className="montage-number"><span>{label}</span><input type="text" inputMode="decimal" aria-label={label} aria-describedby={hint?helpId:undefined} value={draft} disabled={disabled} onChange={e=>setDraft(e.target.value)} onBlur={commit} onKeyDown={e=>{if(e.key==='Enter')e.currentTarget.blur();if(e.key==='ArrowUp' || e.key==='ArrowDown'){e.preventDefault();const next=Math.max(min,Math.min(max,value+(e.key==='ArrowUp'?step:-step)));onCommit(Math.round(next*1000)/1000);}}}/>{hint && <small id={helpId}>{hint}</small>}</label>;
}
function TrimWave({recording,edit,position,onChange,onStart,onSeek,ru}:{recording:Recording;edit:Required<ClipEdit>;position:number;onChange:(patch:Partial<ClipEdit>)=>void;onStart:()=>void;onSeek:(seconds:number)=>void;ru:boolean}){
  const container=useRef<HTMLDivElement>(null),drag=useRef<'start'|'end'|null>(null);
  const update=(clientX:number,key:'start'|'end')=>{const rect=container.current!.getBoundingClientRect();const value=Math.round(Math.max(0,Math.min(1,(clientX-rect.left)/rect.width))*recording.duration*100)/100;onChange(key==='start'?{start:Math.min(value,edit.end-.08)}:{end:Math.max(value,edit.start+.08)});};
  const start=(event:PointerEvent<HTMLButtonElement>,key:'start'|'end')=>{event.stopPropagation();onStart();drag.current=key;event.currentTarget.setPointerCapture(event.pointerId);update(event.clientX,key);};
  return <div className="trim-wave" ref={container}>
    <Wave peaks={recording.peaks} progress={position/recording.duration}/>
    <input className="trim-seek" type="range" min={0} max={recording.duration} step={.01} value={Math.min(recording.duration,position)} aria-label={ru?'Позиция в исходной записи':'Position in original recording'} onChange={e=>onSeek(Number(e.target.value))}/>
    <span className="trim-discard trim-discard-start" style={{width:`${edit.start/recording.duration*100}%`}}/><span className="trim-discard trim-discard-end" style={{width:`${(1-edit.end/recording.duration)*100}%`}}/>
    {(['start','end'] as const).map(key=><button type="button" key={key} className={`trim-handle trim-${key}`} role="slider" aria-label={ru?key==='start'?'Начало фрагмента':'Конец фрагмента':key==='start'?'Clip start':'Clip end'} aria-valuemin={key==='start'?0:edit.start+.08} aria-valuemax={key==='end'?recording.duration:edit.end-.08} aria-valuenow={edit[key]} aria-valuetext={`${edit[key].toFixed(2)} ${ru?'с':'s'}`} style={{left:`${edit[key]/recording.duration*100}%`}} onPointerDown={event=>start(event,key)} onPointerMove={event=>{if(drag.current===key)update(event.clientX,key);}} onPointerUp={()=>drag.current=null} onLostPointerCapture={()=>drag.current=null} onKeyDown={event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();onStart();const min=key==='start'?0:edit.start+.08,max=key==='end'?recording.duration:edit.end-.08;const value=event.key==='Home'?min:event.key==='End'?max:edit[key]+(event.key==='ArrowLeft'?-1:1)*(event.shiftKey ? .1 : .01);onChange({[key]:Math.round(Math.max(min,Math.min(max,value))*1000)/1000});}}><span/></button>)}
  </div>;
}
export function AssemblyPanel({project,setProject,projectId,recordings,selected,choose,locale,montage,pausePlayback,openText,cleanScene,cleanFinal}:{cleanScene:()=>void;cleanFinal:()=>void;project:Project;setProject:Dispatch<SetStateAction<Project>>;projectId:string|null;recordings:Recording[];selected:string;choose:(id:string)=>void;locale:Locale;montage:ReturnType<typeof useAssembly>;pausePlayback:(element?:HTMLAudioElement)=>void;openText:()=>void}){
  const ru=locale==='ru',L=(a:string,b:string)=>ru?a:b,items=arrangement(project,recordings),item=items.find(i=>i.scene.id===selected)??items[0];
  const source=useRef<HTMLAudioElement>(null),[position,setPosition]=useState(0),[format,setFormat]=useState('wav'),[previewGain,setPreviewGain]=useState<number|null>(null);
  const [history,setHistory]=useState<ReturnType<typeof audioSnapshot>[]>([]),[future,setFuture]=useState<ReturnType<typeof audioSnapshot>[]>([]);
  const historyKey=JSON.stringify([projectId,project.scenes.map(s=>[s.id,sourceId(s)]).sort()]);
  useEffect(()=>{setHistory([]);setFuture([]);},[historyKey]);
  useEffect(()=>{setPosition(0);setPreviewGain(null);},[item?.scene.id,item?.recording?.id]);
  const checkpoint=()=>{setHistory(h=>[...h.slice(-39),audioSnapshot(project)]);setFuture([]);};
  const change=(edit:(p:Project)=>Project)=>{checkpoint();setProject(edit);};
  const sceneChange=(patch:Partial<NonNullable<Scene['assembly']>>)=>{if(item)change(p=>({...p,scenes:p.scenes.map(s=>s.id===item.scene.id?{...s,assembly:{...s.assembly,...patch}}:s)}));};
  const trim=(patch:Partial<ClipEdit>,save=true)=>{if(!item?.recording)return;if(save)checkpoint();setProject(p=>setClipEdit(p,item.scene.id,item.recording!.id,patch));};
  const undo=(redo=false)=>{const stack=redo?future:history,last=stack.at(-1);if(!last)return;(redo?setHistory:setFuture)(h=>[...h,audioSnapshot(project)]);(redo?setFuture:setHistory)(h=>h.slice(0,-1));setProject(p=>restoreAudio(p,last));};
  const reorder=(id:string,target:string,after:boolean)=>{
    const remaining=project.scenes.filter(s=>s.id!==id),source=project.scenes.find(s=>s.id===id),index=remaining.findIndex(s=>s.id===target);
    if(!source || index<0 || id===target)return;
    remaining.splice(index+(after?1:0),0,source);
    if(remaining.every((s,i)=>s.id===project.scenes[i].id))return;
    change(p=>({...p,scenes:remaining}));
  };
  const missing=items.filter(i=>!i.excluded && !i.recording),included=items.filter(i=>!i.excluded && i.recording),valid=included.length>0 && missing.length===0 && !items.some(i=>!i.excluded && i.edit && (i.edit.end-i.edit.start<.08-1e-6 || i.edit.end>i.recording!.duration+.025));
  const duration=included.at(-1)?.end??0;
  const seekSource=(seconds:number)=>{const el=source.current;if(!el || !item?.edit)return;el.currentTime=Math.max(item.edit.start,Math.min(item.edit.end,seconds));setPosition(el.currentTime);};
  return <section className="assembly-workbench" aria-label={L('Монтаж итогового аудио','Final audio montage')}>
    <aside className="assembly-scenes panel"><div className="assembly-panel-heading"><h2>{L('Порядок сцен','Scene order')}</h2><div className="assembly-history"><button type="button" className="icon-button" disabled={!history.length} aria-label={L('Отменить монтажное изменение','Undo montage change')} title={L('Отменить','Undo')} onClick={()=>undo()}><ArrowCounterClockwise size={18} aria-hidden="true"/><span>{L('Отмена','Undo')}</span></button><button type="button" className="icon-button" disabled={!future.length} aria-label={L('Повторить монтажное изменение','Redo montage change')} title={L('Повторить','Redo')} onClick={()=>undo(true)}><ArrowClockwise size={18} aria-hidden="true"/><span>{L('Повтор','Redo')}</span></button></div></div>
      <SceneOrderList items={items} selected={item?.scene.id} ru={ru} choose={choose} toggle={(scene,excluded)=>change(p=>({...p,scenes:p.scenes.map(s=>s.id===scene.id?{...s,assembly:{...s.assembly,excluded}}:s)}))} reorder={reorder}/>
      <p className="assembly-help">{L('Перетаскивайте сцены за ручку слева. Галочка включает сцену в итог.','Drag scenes by the handle on the left. Check a scene to include it.')}</p>
    </aside>
    <div className="assembly-editor panel"><div className="assembly-panel-heading"><h2><Scissors size={18} aria-hidden="true"/>{item?.scene.title||L('Выберите сцену','Select a scene')}</h2><div className="assembly-header-actions">{item?.recording && <span className="assembly-duration">{audioTime(item.duration)}</span>}<Menu label={L('Действия с дублем','Take actions')} icon={DotsThree} className="take-actions-menu"><button type="button" disabled={!item?.recording} onClick={cleanScene}>{L('Улучшить выбранный дубль','Enhance selected take')}</button></Menu></div></div>
      <div className="assembly-editor-body">{item?.recording && item.edit?<>
        {((item.scene.takeIds?.length??0)+(item.scene.audioIndex!=null?1:0))>1 && <label className="field"><span>{L('Дубль для монтажа','Take to edit')}</span><Select label={L('Дубль для монтажа','Take to edit')} value={item.recording.id} options={recordings.filter((r,index)=>item.scene.takeIds?.includes(r.id) || !r.generated && item.scene.audioIndex===index).map(r=>({value:r.id,label:r.generated?`${L('Дубль','Take')} ${item.scene.takeIds!.indexOf(r.id)+1} / ${audioTime(r.duration)}`:L('Исходная запись','Original recording')}))} onChange={id=>setProject(p=>({...p,scenes:p.scenes.map(s=>s.id===item.scene.id?{...s,selectedTakeId:id.startsWith('demo-')?undefined:id}:s)}))}/></label>}
        <p className="assembly-help">{L('Потяните края волны, чтобы обрезать запись.','Drag the waveform edges to trim the recording.')}</p>
        <TrimWave recording={item.recording} edit={item.edit} position={position} ru={ru} onStart={checkpoint} onChange={patch=>trim(patch,false)} onSeek={seekSource}/>
        <div className="trim-ruler"><span>0:00</span><span>{audioTime(item.recording.duration)} {L('исходник','original')}</span></div>
        <AudioPlayer key={`${item.scene.id}:${item.recording.id}`} src={item.recording.url} mediaRef={source} label={L('Выбранный фрагмент','Selected excerpt')} locale={locale} onPlay={pausePlayback} range={item.edit} gainDb={previewGain??item.edit.gainDb} hideWave onPosition={setPosition}/>
        <div className="assembly-inline-actions"><button type="button" className="quiet" disabled={item.edit.start===0 && item.edit.end===item.recording.duration} onClick={()=>trim({start:0,end:item.recording!.duration})}><ArrowCounterClockwise size={17}/>{L('Вернуть целую запись','Restore full recording')}</button></div>
        <div className="assembly-fields"><SceneGain value={item.edit.gainDb} ru={ru} onPreview={setPreviewGain} onCommit={gainDb=>trim({gainDb})}/><NumberField label={L('Пауза до следующей сцены, с','Pause before next scene, s')} hint={included.at(-1)?.scene.id===item.scene.id?L('После последней сцены паузы нет.','There is no pause after the last scene.'):L('Тишина до следующей сцены.','Silence before the next scene.')} value={included.at(-1)?.scene.id===item.scene.id?0:item.scene.assembly?.pauseAfter??project.mix?.gapSeconds??.25} min={0} max={5} step={.05} disabled={included.at(-1)?.scene.id===item.scene.id} onCommit={pauseAfter=>sceneChange({pauseAfter})}/></div>
        <div className="assembly-inline-actions"><button type="button" className="quiet" disabled={!valid || montage.busy || item.excluded || included.at(-1)?.scene.id===item.scene.id} onClick={()=>void montage.join(item.scene.id)}><Play size={16}/>{L('Послушать переход','Preview transition')}</button>{item.scene.assembly?.pauseAfter!=null && <button type="button" className="text-link" onClick={()=>sceneChange({pauseAfter:undefined})}>{L('Вернуть общую паузу','Use default pause')}</button>}</div>
        {item.excluded && <p className="assembly-help" role="status">{L('Эта сцена исключена. Включите её галочкой в списке.','This scene is excluded. Check it in the list to include it.')}</p>}
        <details className="assembly-transcript"><summary>{L('Текст выбранного дубля','Selected take text')}</summary><p>{item.recording.sourceText??item.scene.text}</p></details>
      </>:<div className="assembly-empty"><p>{L('В этой сцене пока нет записи.','This scene has no recording yet.')}</p>{item && <button type="button" className="quiet" onClick={openText}>{L('Перейти к озвучке','Open speech editor')}</button>}</div>}</div>
    </div>
    <aside className="assembly-output panel"><div className="assembly-panel-heading"><h2>{L('Собрать все сцены','Assemble all scenes')}</h2><div className="assembly-header-actions"><span className="assembly-duration">{audioTime(montage.result?.duration??duration)}</span><Menu label={L('Действия с итогом','Master actions')} icon={DotsThree} className="take-actions-menu"><button type="button" disabled={!valid || montage.busy} onClick={cleanFinal}>{L('Улучшить итоговую запись','Enhance final recording')}</button></Menu></div></div>
      <div className="assembly-output-settings"><NumberField label={L('Пауза между сценами, с','Pause between scenes, s')} hint={L('Если у сцены не задана своя пауза.','Used unless a scene has its own pause.')} value={project.mix?.gapSeconds??.25} min={0} max={5} step={.05} onCommit={gapSeconds=>change(p=>({...p,mix:{...p.mix,gapSeconds}}))}/>
      <label className="assembly-toggle"><input type="checkbox" checked={project.mix?.leveling!==false} onChange={e=>{const leveling=e.target.checked;change(p=>({...p,mix:{...p.mix,leveling}}));}}/><span>{L('Выровнять громкость сцен','Match scene loudness')}<small>{L('Уменьшает перепады громкости.','Reduces volume differences.')}</small></span></label>
      <label className="assembly-toggle"><input type="checkbox" checked={project.mix?.softEdges!==false} onChange={e=>{const softEdges=e.target.checked;change(p=>({...p,mix:{...p.mix,softEdges}}));}}/><span>{L('Смягчить края фрагментов','Soften clip edges')}<small>{L('Меньше щелчков на срезах.','Reduces clicks at cuts.')}</small></span></label>
      {!!missing.length && <div className="assembly-warning" role="status"><p>{L(`Без записи: ${missing.length}. Озвучьте или исключите эти сцены.`,`${missing.length} scenes have no recording. Generate or exclude them.`)}</p><button type="button" className="text-link" onClick={()=>change(p=>({...p,scenes:p.scenes.map(s=>missing.some(i=>i.scene.id===s.id)?{...s,assembly:{...s.assembly,excluded:true}}:s)}))}>{L('Исключить сцены без записи','Exclude unrecorded scenes')}</button></div>}
      {!included.length && !missing.length && <p className="assembly-help">{L('Включите хотя бы одну сцену.','Include at least one scene.')}</p>}
      </div><div className="assembly-output-actions"><button type="button" className="primary" disabled={!valid || montage.busy} onClick={()=>void montage.preview(0)}><Play size={18} weight="fill"/>{montage.busy?L('Собираем аудио…','Assembling audio…'):L('Слушать итог','Listen to final audio')}</button>
      <div className="assembly-download"><Select label={L('Формат итоговой записи','Final audio format')} value={format} onChange={setFormat} options={[{value:'wav',label:'WAV / 48 kHz'},{value:'mp3',label:'MP3 / 192 kbps'}]}/><button type="button" className="quiet" disabled={!valid || montage.busy} onClick={()=>void montage.download(format as 'wav'|'mp3')}><DownloadSimple size={18}/>{L('Скачать','Download')}</button></div>
      <p className="assembly-help" role="status">{montage.result?L('Итог собран. Изменения потребуют новой сборки.','Final audio is ready. Changes require rebuilding.'):L('Паузы и обрезка сохраняются в проекте. Итог собирается по нажатию.','Cuts and pauses are saved in the project. Final audio builds on request.')}</p>
      {montage.error && <p className="generation-error" role="alert">{montage.error}</p>}</div>
    </aside>
  </section>;
}
