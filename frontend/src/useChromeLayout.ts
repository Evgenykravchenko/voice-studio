import {useLayoutEffect,useState,type RefObject} from 'react';

/** Reserve the exact painted dock size, including wrapping and the device safe area. */
export function useChromeLayout(header:RefObject<HTMLElement|null>,dock:RefObject<HTMLElement|null>,dockKey:string){
  const [short,setShort]=useState(()=>innerHeight<500);
  useLayoutEffect(()=>{
    const root=document.documentElement;
    const measure=()=>{
      root.style.setProperty('--app-header-height',`${header.current?.getBoundingClientRect().height??0}px`);
      root.style.setProperty('--playback-height',`${dock.current?.getBoundingClientRect().height??0}px`);
    };
    const viewport=()=>{
      const height=visualViewport?.height??innerHeight;
      const field=document.activeElement;
      const editing=field instanceof HTMLTextAreaElement || field instanceof HTMLInputElement && !['range','file','button'].includes(field.type);
      root.dataset.keyboardOpen=String(editing && height<innerHeight*.75);
      setShort(height<500);measure();
    };
    const observer=new ResizeObserver(measure);
    if(header.current)observer.observe(header.current);
    if(dock.current)observer.observe(dock.current);
    viewport();
    addEventListener('resize',viewport);visualViewport?.addEventListener('resize',viewport);
    document.addEventListener('focusin',viewport);document.addEventListener('focusout',viewport);
    return()=>{observer.disconnect();removeEventListener('resize',viewport);visualViewport?.removeEventListener('resize',viewport);document.removeEventListener('focusin',viewport);document.removeEventListener('focusout',viewport);};
  },[header,dock,dockKey]);
  return short;
}
