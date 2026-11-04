import type {Project,Scene,Recording,ClipEdit} from './types';
export const sourceId=(s:Scene)=>s.selectedTakeId ?? (s.audioIndex==null?undefined:`demo-${s.audioIndex}`);
export function sceneRecording(s:Scene,recordings:Recording[]){const id=sourceId(s);return recordings.find(r=>r.id===id && r.available!==false);}
export function clipEdit(s:Scene,r:Recording):Required<ClipEdit>{const e=s.assembly?.edits?.[r.id];return {start:e?.start??0,end:e?.end??r.duration,gainDb:e?.gainDb??0};}
export function arrangement(project:Project,recordings:Recording[]){
  let position=0;const included=project.scenes.filter(s=>!s.assembly?.excluded);
  return project.scenes.map(scene=>{const recording=sceneRecording(scene,recordings),edit=recording?clipEdit(scene,recording):undefined;
    const excluded=!!scene.assembly?.excluded,duration=edit?Math.max(0,edit.end-edit.start):0;
    const gap=excluded || included.at(-1)?.id===scene.id?0:scene.assembly?.pauseAfter??project.mix?.gapSeconds??.25;
    const start=position;if(!excluded && recording)position+=duration+gap;
    return {scene,recording,edit,duration,start,end:start+(excluded?0:duration),gap,excluded};});
}
export function audioSignature(project:Project){return JSON.stringify({mix:{gapSeconds:project.mix?.gapSeconds??.25,leveling:project.mix?.leveling!==false,softEdges:project.mix?.softEdges!==false},scenes:project.scenes.filter(s=>!s.assembly?.excluded).map(s=>{const id=sourceId(s);return {id:s.id,sourceId:id,edit:id?s.assembly?.edits?.[id]:undefined,pause:s.assembly?.pauseAfter};})});}
export function croppedPeaks(peaks:number[],start:number,end:number,duration:number){return peaks.slice(Math.floor(start/duration*peaks.length),Math.max(1,Math.ceil(end/duration*peaks.length)));}
export function setClipEdit(project:Project,sceneId:string,id:string,patch:Partial<ClipEdit>){return {...project,scenes:project.scenes.map(s=>s.id===sceneId?{...s,assembly:{...s.assembly,edits:{...s.assembly?.edits,[id]:{start:0,...s.assembly?.edits?.[id],...patch}}}}:s)};}
export function audioSnapshot(project:Project){return {order:project.scenes.map(s=>s.id),mix:structuredClone(project.mix),assembly:Object.fromEntries(project.scenes.map(s=>[s.id,structuredClone(s.assembly)]))};}
export function restoreAudio(project:Project,snapshot:ReturnType<typeof audioSnapshot>):Project {const order=new Map(snapshot.order.map((id,i)=>[id,i]));return {...project,mix:snapshot.mix,scenes:project.scenes.map(s=>s.id in snapshot.assembly?{...s,assembly:snapshot.assembly[s.id]}:s).sort((a,b)=>(order.get(a.id)??Infinity)-(order.get(b.id)??Infinity))};}
