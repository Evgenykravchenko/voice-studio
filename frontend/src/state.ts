import type { Project, Scene, Theme, Locale } from './types';
export const initialProject: Project = {
  title: 'Новый проект',
  scenes: [{ id: 'first-scene', title: 'Первая сцена', text: '', audioIndex: null,
    speechLanguage: 'auto', emotion: 'calm', temperature: 0.8, seed: '' }],
};
export function readStored<T>(key: string, fallback: T, validate: (v: unknown) => v is T): T {
  try { const value: unknown = JSON.parse(localStorage.getItem(key) ?? 'null'); return validate(value) ? value : fallback; }
  catch { return fallback; }
}
export const isTheme = (v: unknown): v is Theme => v === 'light' || v === 'dark' || v === 'system';
export const isLocale = (v: unknown): v is Locale => v === 'ru' || v === 'en';
const bounded = (v: unknown,min:number,max:number) => typeof v==='number' && Number.isFinite(v) && v>=min && v<=max;
function isAssembly(v:unknown):boolean {
  if(v===undefined || v===null)return true;
  if(!v || typeof v!=='object')return false;
  const a=v as import('./types').SceneAssembly;
  return (a.excluded==null || typeof a.excluded==='boolean') && (a.pauseAfter==null || bounded(a.pauseAfter,0,5))
    && (a.edits==null || typeof a.edits==='object' && !Array.isArray(a.edits) && Object.entries(a.edits).length<=103 && Object.entries(a.edits).every(([key,e])=>/^(demo-[0-2]|[0-9a-f-]{36})$/.test(key) && !!e && bounded(e.start,0,7200) && (e.end==null || bounded(e.end,0,7200) && e.end-e.start>=.08-1e-6) && (e.gainDb==null || bounded(e.gainDb,-18,12))));
}
function isMix(v:unknown):boolean {
  if(v==null)return true;
  if(typeof v!=='object' || Array.isArray(v))return false;
  const m=v as import('./types').MixSettings;
  return (m.gapSeconds==null || bounded(m.gapSeconds,0,5)) && (m.leveling==null || typeof m.leveling==='boolean') && (m.softEdges==null || typeof m.softEdges==='boolean');
}
function isScene(v: unknown): v is Scene {
  if (!v || typeof v !== 'object') return false;
  const s = v as Scene;
  return typeof s.id === 'string' && typeof s.title === 'string' && typeof s.text === 'string'
    && typeof s.speechLanguage === 'string' && /^(auto|[a-z]{2,3}(?:-[A-Za-z0-9]+)?)$/.test(s.speechLanguage) && ['calm','excited','whisper','laughing','angry'].includes(s.emotion)
    && typeof s.temperature === 'number' && s.temperature >= 0.1 && s.temperature <= 1.5 && typeof s.seed === 'string'
    && (s.audioIndex === null || (Number.isInteger(s.audioIndex) && s.audioIndex >= 0 && s.audioIndex < 3))
    && (s.voiceId === undefined || (typeof s.voiceId === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(s.voiceId)))
    && (s.presetVoice === undefined || (typeof s.presetVoice === 'string' && s.presetVoice.length <= 64))
    && (s.voiceDescription === undefined || (typeof s.voiceDescription === 'string' && s.voiceDescription.length <= 1000))
    && (s.voiceMode === undefined || ['clone','preset','design','effect'].includes(s.voiceMode))
    && (s.takeIds === undefined || (Array.isArray(s.takeIds) && s.takeIds.length <= 100 && s.takeIds.every(id => typeof id === 'string' && /^[0-9a-f-]{36}$/.test(id))))
    && isAssembly(s.assembly)
    && (s.selectedTakeId === undefined || (typeof s.selectedTakeId === 'string' && /^[0-9a-f-]{36}$/.test(s.selectedTakeId)));
}
export const isProject = (v: unknown): v is Project => !!v && typeof v === 'object'
  && isMix((v as Project).mix)
  && typeof (v as Project).title === 'string' && Array.isArray((v as Project).scenes)
  && (v as Project).scenes.every(isScene) && new Set((v as Project).scenes.map(s => s.id)).size === (v as Project).scenes.length;
