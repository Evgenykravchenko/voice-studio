import {useEffect,useRef,useState,type PointerEvent,type KeyboardEvent} from 'react';
import {DotsSixVertical} from '@phosphor-icons/react';
import type {Scene} from './types';
import type {arrangement} from './assembly-utils';
import {audioTime} from './audio-utils';

type Drop={id:string;target:string;after:boolean;keyboard:boolean};
export function SceneOrderList({items,selected,ru,choose,toggle,reorder}:{
  items:ReturnType<typeof arrangement>;selected?:string;ru:boolean;
  choose:(id:string)=>void;toggle:(scene:Scene,excluded:boolean)=>void;
  reorder:(id:string,target:string,after:boolean)=>void;
}){
  const list=useRef<HTMLDivElement>(null),pointer=useRef<{id:string;x:number;y:number;pointerId:number;active:boolean}|null>(null);
  const [drop,setDrop]=useState<Drop|null>(null),current=useRef<Drop|null>(null),[notice,setNotice]=useState('');
  const update=(value:Drop|null)=>{const previous=current.current;if(previous===value || previous && value && previous.id===value.id && previous.target===value.target && previous.after===value.after && previous.keyboard===value.keyboard)return;current.current=value;setDrop(value);};
  const label=(id:string)=>items.find(i=>i.scene.id===id)?.scene.title|| (ru?'Без названия':'Untitled');
  const cancel=()=>{pointer.current=null;update(null);};
  // Captured pointer events still hit-test the actual row beneath the handle.
  const locate=(x:number,y:number)=>{
    const row=document.elementsFromPoint(x,y).map(e=>e.closest<HTMLElement>('[data-order-scene]')).find(e=>e && list.current?.contains(e));
    if(!row || !pointer.current?.active){update(null);return;}
    const target=row.dataset.orderScene!,rect=row.getBoundingClientRect();
    update(target===pointer.current.id?null:{id:pointer.current.id,target,after:y>rect.top+rect.height/2,keyboard:false});
  };
  useEffect(()=>{
    if(!drop || drop.keyboard)return;
    let frame=0;
    const scroll=()=>{const el=list.current,p=pointer.current;if(el && p?.active){const r=el.getBoundingClientRect();const speed=p.y<r.top+32?-7:p.y>r.bottom-32?7:0;if(speed && p.y>r.top-24 && p.y<r.bottom+24){const before=el.scrollTop;el.scrollTop+=speed;if(el.scrollTop!==before)locate(p.x,p.y);}}frame=requestAnimationFrame(scroll);};
    frame=requestAnimationFrame(scroll);return()=>cancelAnimationFrame(frame);
  },[!!drop,drop?.keyboard]);
  const identity=items.map(i=>i.scene.id).join(':');
  useEffect(()=>{cancel();},[identity]);
  useEffect(()=>{const escape=(e:globalThis.KeyboardEvent)=>{if(e.key==='Escape' && (pointer.current || current.current)){cancel();setNotice(ru?'Перемещение отменено':'Reorder cancelled');}};addEventListener('keydown',escape);return()=>removeEventListener('keydown',escape);},[ru]);
  const down=(e:PointerEvent<HTMLButtonElement>,id:string)=>{
    if(e.button!==0 || !e.isPrimary)return;
    update(null);pointer.current={id,x:e.clientX,y:e.clientY,pointerId:e.pointerId,active:false};
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const move=(e:PointerEvent<HTMLButtonElement>)=>{const p=pointer.current;if(!p || p.pointerId!==e.pointerId)return;
    if(!p.active && Math.hypot(e.clientX-p.x,e.clientY-p.y)<6)return;
    p.active=true;p.x=e.clientX;p.y=e.clientY;locate(e.clientX,e.clientY);
  };
  const finish=()=>{const target=current.current;if(pointer.current?.active && target){reorder(target.id,target.target,target.after);setNotice(ru?`Сцена «${label(target.id)}» перемещена`:`Scene “${label(target.id)}” moved`);}cancel();};
  const keyboard=(event:KeyboardEvent<HTMLButtonElement>,id:string)=>{
    const active=current.current?.keyboard && current.current.id===id;
    if(event.key===' ' || event.key==='Enter'){
      event.preventDefault();
      if(active){const target=current.current!;if(target.target!==id)reorder(id,target.target,target.after);cancel();setNotice(ru?'Порядок сцен сохранён':'Scene order saved');}
      else{pointer.current=null;update({id,target:id,after:false,keyboard:true});setNotice(ru?'Выберите место стрелками. Пробел — поставить, Escape — отменить.':'Choose a position with arrow keys. Space to drop, Escape to cancel.');}
    }else if(active && ['ArrowUp','ArrowDown','Home','End'].includes(event.key)){
      event.preventDefault();const original=items.findIndex(i=>i.scene.id===id),d=current.current!;
      const remaining=items.filter(i=>i.scene.id!==id),targetIndex=d.target===id?original:remaining.findIndex(i=>i.scene.id===d.target)+(d.after?1:0);
      const index=event.key==='Home'?0:event.key==='End'?remaining.length:Math.max(0,Math.min(remaining.length,targetIndex+(event.key==='ArrowUp'?-1:1)));
      const target=remaining[Math.min(index,remaining.length-1)];if(!target)return;
      update({id,target:target.scene.id,after:index===remaining.length,keyboard:true});setNotice(ru?`Позиция ${index+1} из ${items.length}`:`Position ${index+1} of ${items.length}`);
    }
  };
  return <><div className="assembly-scene-list" ref={list} aria-label={ru?'Порядок сцен':'Scene order'}>{items.map((entry,index)=><div className={`assembly-scene ${entry.scene.id===selected?'assembly-selected':''}`} key={entry.scene.id} data-order-scene={entry.scene.id} data-excluded={entry.excluded} data-dragging={drop?.id===entry.scene.id || pointer.current?.active && pointer.current.id===entry.scene.id || undefined} data-drop={drop?.target===entry.scene.id && drop.id!==drop.target?(drop.after?'after':'before'):undefined}>
    <button type="button" className="scene-drag-handle" disabled={items.length<2} aria-label={`${ru?'Перетащить сцену':'Move scene'}: ${label(entry.scene.id)}`} title={ru?'Перетащите, чтобы изменить порядок':'Drag to reorder'} aria-describedby="scene-drag-instructions" aria-pressed={drop?.keyboard && drop.id===entry.scene.id || false} onPointerDown={e=>down(e,entry.scene.id)} onPointerMove={move} onPointerUp={finish} onPointerCancel={cancel} onLostPointerCapture={()=>{if(pointer.current)cancel();}} onKeyDown={e=>keyboard(e,entry.scene.id)}><DotsSixVertical size={18} aria-hidden="true"/></button>
    <label className="assembly-check"><input type="checkbox" checked={!entry.excluded} aria-label={`${ru?'Включить в итог':'Include in final audio'}: ${label(entry.scene.id)}`} onChange={e=>toggle(entry.scene,!e.target.checked)}/></label>
    <button type="button" className="assembly-scene-name" aria-pressed={entry.scene.id===selected} onClick={()=>choose(entry.scene.id)}><strong>{index+1}. {label(entry.scene.id)}</strong><small>{entry.excluded?(ru?'Исключена':'Excluded'):entry.recording?`${audioTime(entry.start)} / ${audioTime(entry.duration)}`:(ru?'Нет записи':'No recording')}</small></button>
  </div>)}</div><span id="scene-drag-instructions" className="visually-hidden">{ru?'Перетащите за ручку. С клавиатуры: пробел, стрелки вверх или вниз, пробел для подтверждения; Escape для отмены.':'Drag the handle. With a keyboard: Space, Up or Down, Space to confirm; Escape to cancel.'}</span><span className="visually-hidden" role="status">{notice}</span></>;
}
