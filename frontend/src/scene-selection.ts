/** Keep explicit selection on edits; resolve a new project's deep link after it loads. */
export function resolveSceneSelection(scenes:readonly {id:string}[],selected:string,requested:string|null,projectChanged:boolean):string {
  const exists=(id:string|null)=>id!==null&&scenes.some(scene=>scene.id===id);
  if(!projectChanged&&exists(selected))return selected;
  return exists(requested)?requested!:scenes[0]?.id??'';
}
