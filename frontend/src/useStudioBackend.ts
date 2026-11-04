import { useCallback, useEffect, useRef, useState } from 'react';
import type { EngineHealth, GenerationJob, GenerationRequest, Recording, VoiceProfile } from './types';

// Optional local metadata stays outside Git; a fresh checkout has no private demos.
const demoFiles = import.meta.glob<Array<{ url: string; duration: number; peaks: number[] }>>('./audio-data.json', { eager: true, import: 'default' });
const demo = demoFiles['./audio-data.json'] ?? [];

export async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { ...init, signal: AbortSignal.timeout(init?.body instanceof FormData ? 120000 : 8000), cache: 'no-store' });
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.error || `HTTP ${response.status}`); }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}
export function useStudioBackend() {
  const [health, setHealth] = useState<EngineHealth | null>(null);
  const [connecting, setConnecting] = useState(true);
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [jobs, setJobs] = useState<GenerationJob[]>([]);
  const [recordings, setRecordings] = useState<Recording[]>(() => demo.map((r, i) => ({ ...r, id: `demo-${i}`, title: ['Вступление', 'Как устроен проект', 'Проверка результата'][i], generated: false, available: false })));
  useEffect(() => {
    const controller = new AbortController();
    void Promise.all(demo.map(async recording => {
      try {
        const response = await fetch(recording.url, { method: 'HEAD', signal: controller.signal });
        return response.ok && response.headers.get('content-type')?.startsWith('audio/');
      } catch { return false; }
    })).then(available => {
      if (!controller.signal.aborted) setRecordings(previous => previous.map(recording => recording.generated ? recording : { ...recording, available: !!available[Number(recording.id.replace('demo-', ''))] }));
    });
    return () => controller.abort();
  }, []);
  const mounted = useRef(true);
  const active = useRef<GenerationJob[]>([]);
  const registerRecordings=useCallback((incoming:GenerationJob[])=>{
    if(!mounted.current)return;
    setRecordings(previous=>{
      const next=[...previous];
      for(const job of incoming.filter(j=>j.status==='succeeded' && j.result).sort((a,b)=>a.createdAt.localeCompare(b.createdAt))){
        if(!next.some(r=>r.id===job.id) && job.result)next.push({...job.result,title:job.request.title,createdAt:job.createdAt,projectId:job.request.projectId,sceneId:job.request.sceneId,voiceId:job.request.voiceId,modelId:job.request.modelId,presetVoice:job.request.presetVoice,voiceDescription:job.request.voiceDescription,sourceText:job.request.text,emotion:job.request.emotion,generated:true});
      }
      return next.length===previous.length?previous:next;
    });
  },[]);
  const merge = useCallback((incoming: GenerationJob[]) => {
    if (!mounted.current) return;
    setJobs(previous => {
      const next = [...previous];
      for (const job of incoming) { const index = next.findIndex(j => j.id === job.id); if (index === -1) next.push(job); else next[index] = job; }
      active.current = next.filter(j => j.status === 'queued' || j.status === 'running');
      return next;
    });
    registerRecordings(incoming);
  }, [registerRecordings]);
  useEffect(() => {
    mounted.current = true;
    let connected = false, checking = false, polling = false;
    const connect = async () => {
      if (checking) return; checking = true;
      try {
        const next = await request<EngineHealth>('/api/health');
        if (!mounted.current) return;
        setHealth(next);
        if (!connected) {
          const [history, profiles] = await Promise.all([request<GenerationJob[]>('/api/jobs'), request<VoiceProfile[]>('/api/voices')]);
          if (!mounted.current) return;
          merge(history); setVoices(profiles); connected = true;
        } else {
          const profiles=await request<VoiceProfile[]>('/api/voices');
          if(mounted.current)setVoices(profiles);
        }
      } catch { connected = false; if (mounted.current) setHealth(null); }
      finally { checking = false; if (mounted.current) setConnecting(false); }
    };
    const poll = async () => {
      if (polling || !active.current.length) return; polling = true;
      try { const values = await Promise.all(active.current.map(j => request<GenerationJob>(`/api/jobs/${j.id}`))); merge(values); }
      catch { if (mounted.current) setHealth(null); connected = false; }
      finally { polling = false; }
    };
    void connect();
    const heartbeat = setInterval(() => void connect(), 5000);
    const progress = setInterval(() => void poll(), 1200);
    return () => { mounted.current = false; clearInterval(heartbeat); clearInterval(progress); };
  }, [merge]);
  const submit = async (body: GenerationRequest) => {
    const job = await request<GenerationJob>('/api/jobs', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
    merge([job]); return job;
  };
  const requestedRecordings=useRef(new Set<string>());
  const ensureRecordings=useCallback(async(ids:string[])=>{
    const missing=[...new Set(ids)].filter(id=>!requestedRecordings.current.has(id));
    missing.forEach(id=>requestedRecordings.current.add(id));
    for(let start=0;start<missing.length;start+=100){
      const batch=missing.slice(start,start+100);
      try{registerRecordings(await request<GenerationJob[]>(`/api/jobs?ids=${batch.join(',')}`));}
      catch{batch.forEach(id=>requestedRecordings.current.delete(id));}
    }
  },[registerRecordings]);
  const refreshVoices = async () => { const profiles = await request<VoiceProfile[]>('/api/voices'); if (mounted.current) setVoices(profiles); };
  const deleteVoice = async (id: string) => {
    try { await request(`/api/voices/${encodeURIComponent(id)}`, {method:'DELETE'}); }
    catch(error) { await refreshVoices().catch(()=>{}); throw error; }
    if(mounted.current)setVoices(previous=>previous.filter(voice=>voice.id!==id));
  };
  return { health, connecting, voices, jobs, recordings, submit, refreshVoices, deleteVoice, ensureRecordings, registerRecordings };
}
