import type { TranslationKey } from './i18n';

export const AUDIO_ACCEPT = '.wav,.mp3,.m4a,.flac,.ogg,.aac,.aiff,.aif,.opus,.webm';
export const MAX_AUDIO_BYTES = 50 * 1024 * 1024;
export type VoiceField = 'name' | 'file' | 'start' | 'duration' | 'transcript';
export type VoiceErrors = Partial<Record<VoiceField, TranslationKey>>;
export interface RecordingFile { name: string; size: number }
export function recordingError(file: RecordingFile | null): TranslationKey | undefined {
  if (!file) return 'recordingRequired';
  if (file.size <= 0) return 'audioEmpty';
  if (file.size > MAX_AUDIO_BYTES) return 'audioTooLarge';
  if (!/\.(wav|mp3|m4a|flac|ogg|aac|aiff|aif|opus|webm)$/i.test(file.name)) return 'audioUnsupported';
}
export function nameError(name: string): TranslationKey | undefined {
  if (!name.trim()) return 'voiceNameRequired';
  if (name.trim().length > 80) return 'voiceNameTooLong';
}
export function validateVoiceForm(input: { name: string; file: RecordingFile | null; start: string; duration: string }): VoiceErrors {
  const errors: VoiceErrors = {};
  const name = nameError(input.name), file = recordingError(input.file);
  if (name) errors.name = name;
  if (file) errors.file = file;
  if (!input.start.trim() || !Number.isFinite(Number(input.start)) || Number(input.start) < 0 || Number(input.start) > 86400) errors.start = 'invalidClipStart';
  if (!input.duration.trim() || !Number.isFinite(Number(input.duration)) || Number(input.duration) < 5 || Number(input.duration) > 30) errors.duration = 'invalidClipDuration';
  return errors;
}
export function validateVoiceReview(name: string, transcript: string): VoiceErrors {
  const errors: VoiceErrors = {}, invalidName = nameError(name);
  if (invalidName) errors.name = invalidName;
  if (!transcript.trim()) errors.transcript = 'transcriptRequired';
  else if (transcript.length > 5000) errors.transcript = 'transcriptTooLong';
  return errors;
}

export function canTranscribeLanguage(language: string, supported: readonly string[]) {
  return language === 'auto' || supported.includes(language);
}

/** Keep an existing draft visible when the recognizer changes; never change its language. */
export function referenceLanguageOptions(supported: readonly string[], current: string, locale: string, extended: boolean, automaticLabel: string) {
  const codes = [...new Set([...(extended ? supported : ['ru', 'en']), current])].filter(code => code !== 'auto');
  const names = new Intl.DisplayNames([locale], { type: 'language' });
  return [...codes.map(value => {
    let label = value;
    try { label = names.of(value) ?? value; } catch { /* Keep an older draft readable. */ }
    return { value, label: label.charAt(0).toLocaleUpperCase(locale) + label.slice(1) };
  }), { value: 'auto', label: automaticLabel }];
}
