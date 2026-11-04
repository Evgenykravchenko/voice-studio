export type Locale = 'ru' | 'en';
export type Theme = 'dark' | 'light' | 'system';
export type View = 'studio' | 'projects' | 'voices' | 'models' | 'library' | 'cleanup';
export type Emotion = 'calm' | 'excited' | 'whisper' | 'laughing' | 'angry';
export type VoiceMode = 'clone' | 'preset' | 'design' | 'effect';
export interface ClipEdit { start: number; end?: number; gainDb?: number; }
export interface SceneAssembly { excluded?: boolean; pauseAfter?: number; edits?: Record<string, ClipEdit>; }
export interface MixSettings { gapSeconds?: number; leveling?: boolean; softEdges?: boolean; }
export interface Scene {
  id: string; title: string; text: string; speechLanguage: string;
  emotion: Emotion; temperature: number; seed: string; audioIndex: number | null;
  voiceId?: string; voiceMode?: VoiceMode; presetVoice?: string; voiceDescription?: string; takeIds?: string[]; selectedTakeId?: string; assembly?: SceneAssembly;
}
export interface Project { title: string; scenes: Scene[]; mix?: MixSettings; }
export interface GenerationRequest { sceneId: string; projectId?: string; title: string; text: string; voiceId: string | null; voiceMode?: VoiceMode; modelId?: string; presetVoice?: string; voiceDescription?: string; emotion: Emotion; language: Scene['speechLanguage']; seed: number | null; sourceId?: string; durationSeconds?: number; }
export interface GenerationResult { id: string; url: string; duration: number; sampleRate: number; peaks: number[]; seed: number; temperature: number | null; }
export interface GenerationJob {
  id: string; request: GenerationRequest; status: 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  stage: string; part: number; total: number; createdAt: string; completedAt: string | null; error: string | null; result: GenerationResult | null;
}
export interface RecordingPage {items:GenerationJob[];total:number;page:number;size:number}
export interface Recording { available?: boolean; createdAt?:string; projectId?:string; sceneId?:string; voiceId?: string | null; modelId?: string; presetVoice?: string; voiceDescription?: string; id: string; url: string; duration: number; peaks: number[]; title: string; sourceText?: string; seed?: number; emotion?: Emotion; temperature?: number | null; generated: boolean; }
export interface EngineHealth { status: string; supportsTemperature: boolean; supportsVoiceModes?: boolean; supportsReferenceLanguages?: boolean; temperature: number; languageMode: string; maxTextLength: number; }

export interface VoiceProfile { id: string; name: string; engine: string; language: string; referenceText: string; duration: number; referenceUrl: string; }
export interface VoiceImport { modelId?: string | null; id: string; name: string; language: string; status: 'queued' | 'running' | 'ready' | 'saved' | 'failed'; stage: string; transcript: string; duration: number; warnings: string[]; error: string | null; voiceId: string | null; }

export interface CatalogModel {
  resourceBytes?: number;
  resourceReady?: boolean;
  synthesisModes?: VoiceMode[];
  languageMode?: 'text';
  voiceDescriptionExample?: string;
  voiceDescriptionHelp?: {ru:string;en:string};
  voiceDesignControls?: 'spark';
  id: string; name: string; task: 'synthesis' | 'transcription' | 'processing' | 'conversion'; format: string;
  description: { ru: string; en: string }; repo: string; revision: string | null;
  features: string[]; integration: 'ready' | 'files' | 'external'; runtime: string; adapter?: string; markup?: string; supportsSeed?: boolean; defaultTemperature?: number | null;
  downloadable: boolean; gated: boolean; sourceUrl: string; notes?: { ru: string; en: string };
  license: string; languages: string[]; referenceLanguages?: string[]; autoLanguage?: boolean; sizeBytes: number | null; downloadedBytes: number;
  installed: boolean; active: boolean; ready: boolean; runtimeReady: boolean; synthesisMode?: 'clone' | 'preset' | 'design' | 'effect'; presetVoices?: string[];
  status: 'available' | 'queued' | 'downloading' | 'verifying' | 'preparing' | 'installed' | 'failed' | 'cancelled';
  transfer?: { status: string; stage: string; downloadedBytes: number; totalBytes: number; error: string | null };
}
export interface ModelInventory { models: CatalogModel[]; freeBytes: number; supported: boolean; platform: string; }
