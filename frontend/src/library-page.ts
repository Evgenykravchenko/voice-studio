import type {Recording} from './types';
export function libraryPage(recordings:Recording[],query:string,page:number,size:number,source:string){
  const normalize=(value:string)=>value.toLocaleLowerCase().replaceAll('ё','е');
  const needle=normalize(query.trim()),limit=[6,12,24].includes(size)?size:12;
  const all=recordings.map((recording,index)=>({...recording,index})).filter(r=>r.available!==false && (source==='all' || (source==='generated')===!!r.generated) && (!needle || normalize(`${r.title} ${r.sourceText??''}`).includes(needle))).reverse();
  // Keep shipped samples below actual generated takes; source indices never change.
  all.sort((a,b)=>Number(!!b.generated)-Number(!!a.generated));
  const pages=Math.max(1,Math.ceil(all.length/limit)),current=Math.max(1,Math.min(pages,Number.isFinite(page)?Math.floor(page):1));
  return {items:all.slice((current-1)*limit,current*limit),page:current,pages,total:all.length};
}

/** Server pages contain generated audio; locally available samples follow those pages. */
export function pagedLibraryPage(recordings:Recording[],ids:string[],generatedTotal:number,query:string,page:number,size:number,source:string){
  const limit=[6,12,24].includes(size)?size:12;
  const samples=source==='generated'?[]:libraryPage(recordings,query,1,24,'samples').items;
  const generated=source==='samples'?0:generatedTotal;
  const total=generated+samples.length,pages=Math.max(1,Math.ceil(total/limit)),current=Math.max(1,Math.min(pages,page));
  const offset=(current-1)*limit;
  const items=source==='samples' || current!==page?[]:ids.flatMap(id=>{const index=recordings.findIndex(r=>r.id===id);return index<0?[]:[{...recordings[index],index}];});
  const tail=offset+ids.length>=generated?samples.slice(Math.max(0,offset-generated),Math.max(0,offset-generated)+limit-items.length):[];
  return {items:[...items,...tail],page:current,pages,total};
}
