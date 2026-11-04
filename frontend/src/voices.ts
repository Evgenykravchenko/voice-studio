import type { Project } from './types';

type Voice = { id: string };

export function resolveVoiceId(selected: string | undefined, voices: readonly Voice[]): string | undefined {
  // Keep explicit selections even if their profile is temporarily unavailable.
  return selected ?? voices[0]?.id;
}

export function assignDefaultVoice(project: Project, voices: readonly Voice[]): Project {
  const defaultId = voices[0]?.id;
  if (!defaultId || project.scenes.every(scene => scene.voiceId !== undefined)) return project;
  return { ...project, scenes: project.scenes.map(scene => scene.voiceId === undefined ? { ...scene, voiceId: defaultId } : scene) };
}
