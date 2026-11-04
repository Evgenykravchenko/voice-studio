import {Microphone} from '@phosphor-icons/react';
import type {Locale} from './types';
import {arrangement,croppedPeaks} from './assembly-utils';
import {SeekWave} from './Wave';
import {audioTime} from './audio-utils';
const silence=Array<number>(128).fill(0);
export function ProjectTimeline({items,locale,selected,elapsed,active,disabled,progress,choose,seek}:{items:ReturnType<typeof arrangement>;locale:Locale;selected?:string;elapsed:number;active:boolean;disabled:boolean;progress:(index:number)=>number;choose:(id:string)=>void;seek:(seconds:number)=>void}){
  const ru=locale==='ru',format=new Intl.NumberFormat(locale,{maximumFractionDigits:2});
  const recorded=items.filter(i=>!i.excluded && i.recording && i.duration>0),fixed=items.length-recorded.length;
  const scale=Math.min(48,144/Math.max(.1,Math.min(...recorded.map(i=>i.duration),20)));
  const seconds=recorded.reduce((sum,i)=>sum+i.duration+i.gap,0),minWidth=seconds*scale+fixed*144+Math.max(0,items.length-1)*4;
  return <div className="timeline-track" style={{minWidth:`${minWidth}px`}}><div className="clips">{items.map((item,index)=>{
    const hasAudio=!!item.recording && !!item.edit,enabled=hasAudio && !item.excluded,span=item.duration+item.gap;
    const pauseProgress=active && item.gap>0?Math.max(0,Math.min(1,(elapsed-item.end)/item.gap)):0;
    const inPause=active && item.gap>0 && elapsed>=item.end && elapsed<item.end+item.gap;
    const pauseLabel=ru?`Пауза ${format.format(item.gap)} с`:`Pause ${format.format(item.gap)} s`;
    return <div className="timeline-scene-group" key={item.scene.id} style={{flex:enabled?`${span} 0 0`:'0 0 144px',gridTemplateColumns:enabled && item.gap>0?`minmax(0,${item.duration}fr) minmax(0,${item.gap}fr)`:'minmax(0,1fr)'}}>
      <div className={`clip montage-clip ${selected===item.scene.id?'clip-selected':''}`} data-scene-id={item.scene.id} data-excluded={item.excluded} style={{flex:enabled?`${item.duration} 0 0`:'1 0 0'}}>
        <span className="clip-offset">{item.excluded?'—':audioTime(item.start)}</span>
        {hasAudio?<SeekWave disabled={item.excluded || disabled} peaks={croppedPeaks(item.recording!.peaks,item.edit!.start,item.edit!.end,item.recording!.duration)} progress={progress(index)} duration={item.duration} label={`${ru?'Перемотать':'Seek'} — ${item.scene.title}`} onSeek={seconds=>seek(item.start+seconds)}/>:<span className="clip-empty" title={ru?'Нет записи':'No recording'}><Microphone size={18} aria-hidden="true"/></span>}
        <div className="clip-caption"><button type="button" className="clip-label" title={item.scene.title} onClick={()=>choose(item.scene.id)} aria-pressed={selected===item.scene.id}>{item.scene.title||(ru?'Новая сцена':'New scene')}</button></div>
      </div>
      {enabled && item.gap>0 && <div className="timeline-pause" style={{flex:`${item.gap} 0 0`}} data-duration={item.gap} data-active={inPause} title={pauseLabel}>
        <span className="pause-offset">{audioTime(item.end)}</span><SeekWave disabled={disabled} peaks={silence} progress={pauseProgress} duration={item.gap} label={`${pauseLabel} — ${item.scene.title}`} onSeek={seconds=>seek(item.end+seconds)}/><span className="pause-label">{pauseLabel}</span>
        {inPause && <span className="pause-playhead" style={{left:`${pauseProgress*100}%`}} aria-hidden="true"/>}
      </div>}
    </div>;
  })}</div></div>;
}
