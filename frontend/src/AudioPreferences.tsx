import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { SpeakerHigh, SpeakerSlash } from '@phosphor-icons/react';
import type { Locale } from './types';
import { translator } from './i18n';
import { readStored } from './state';

interface Preferences { volume: number; muted: boolean }
const AudioSettings = createContext<{ preferences: Preferences; update: (patch: Partial<Preferences>) => void } | null>(null);
export function AudioPreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState(() => readStored('vs.audio.preferences', { volume: 1, muted: false }, (v): v is Preferences => !!v && typeof v === 'object' && typeof (v as Preferences).volume === 'number' && (v as Preferences).volume >= 0 && (v as Preferences).volume <= 1 && typeof (v as Preferences).muted === 'boolean'));
  useEffect(() => { try { localStorage.setItem('vs.audio.preferences', JSON.stringify(preferences)); } catch { /* Playback remains available without storage. */ } }, [preferences]);
  return <AudioSettings.Provider value={{ preferences, update: patch => setPreferences(value => ({ ...value, ...patch })) }}>{children}</AudioSettings.Provider>;
}
export function useAudioPreferences() {
  const settings = useContext(AudioSettings);
  if (!settings) throw new Error('Missing audio preferences provider');
  return settings;
}
export function VolumeControl({ locale, label }: { locale: Locale; label: string }) {
  const { preferences: { volume, muted }, update } = useAudioPreferences();
  const t = translator(locale), percent = Math.round((muted ? 0 : volume) * 100);
  const toggleMute = () => update({ muted: !(muted || !volume), volume: volume || 1 });
  return <div className="volume-control" role="group" aria-label={`${t('volume')} — ${label}`}>
    <button type="button" className="quiet volume-mute" aria-label={`${t(muted || !volume ? 'unmute' : 'mute')} — ${label}`} aria-pressed={muted || !volume} onClick={toggleMute}>{muted || !volume ? <SpeakerSlash size={20} /> : <SpeakerHigh size={20} />}</button>
    <div className="volume-fader"><span className="volume-track" aria-hidden="true"><span style={{ width: `${percent}%` }} /></span><input className="studio-range volume-range" type="range" min={0} max={1} step={0.01} aria-label={`${t('volume')} — ${label}`} aria-valuetext={`${percent}%`} value={muted ? 0 : volume} onChange={event => update({ volume: Number(event.target.value), muted: false })} /></div>
    <span className="volume-percent" aria-hidden="true">{percent}%</span>
  </div>;
}
