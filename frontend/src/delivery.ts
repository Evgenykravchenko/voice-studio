import type { Emotion } from './types';

const all: Emotion[] = ['calm','excited','whisper','laughing','angry'];
const index: Emotion[] = ['calm','excited','angry'];
const directed = new Set(['fish-s2-pro','qwen3-customvoice','qwen3-voicedesign','moss-voicegenerator','voxcpm2']);

export function deliveryEmotions(modelId?: string): readonly Emotion[] {
  return modelId === 'index-tts2' ? index : modelId && directed.has(modelId) ? all : [];
}

export function effectiveDelivery(modelId: string | undefined, emotion: Emotion): Emotion {
  return deliveryEmotions(modelId).includes(emotion) ? emotion : 'calm';
}

export function deliveryLabel(modelId: string | undefined, emotion: Emotion): 'referenceDelivery' | Emotion {
  return modelId === 'index-tts2' && emotion === 'calm' ? 'referenceDelivery' : emotion;
}
