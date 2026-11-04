import { useEffect, useRef, useState, type RefObject } from 'react';
import { Play, Pause, ArrowCounterClockwise, DotsThree, DownloadSimple, Check } from '@phosphor-icons/react';
import type { Locale } from './types';
import { translator } from './i18n';
import {croppedPeaks} from './assembly-utils';
import { audioTime, waveformPeaks } from './audio-utils';
import { Menu } from './Menu';
import {connectPreview,updatePreview,disconnectPreview} from './audio-preview';
import { SeekWave } from './Wave';
import { VolumeControl, useAudioPreferences } from './AudioPreferences';

const peakCache = new Map<string, number[]>();
let waveformQueue = Promise.resolve();
export function AudioPlayer({ src, label, locale, onPlay, onDuration, downloadName, range, mediaRef, hideWave=false, onPosition, gainDb, restorePlayback,downloadSrc }: {
  restorePlayback?:{seconds:number;playing:boolean}; gainDb?:number; range?: {start:number;end:number}; mediaRef?:RefObject<HTMLAudioElement|null>; hideWave?:boolean; onPosition?:(seconds:number)=>void;
  downloadSrc?:string; src: string; label: string; locale: Locale; downloadName?: string;
  onPlay: (element: HTMLAudioElement) => void; onDuration?: (duration: number) => void;
}) {
  const t = translator(locale), internalMedia = useRef<HTMLAudioElement>(null),media=mediaRef??internalMedia;
  const preview=useRef<ReturnType<typeof connectPreview>|null>(null);
  const [playing, setPlaying] = useState(false), [elapsed, setElapsed] = useState(0), [duration, setDuration] = useState(0);
  const [loading, setLoading] = useState(true), [error, setError] = useState(false);
  const [rate, setRate] = useState(1);
  useEffect(() => { if (media.current) media.current.playbackRate = rate; }, [rate, src]);
  const [waveformError, setWaveformError] = useState(false), [waveformAttempt, setWaveformAttempt] = useState(0);
  const [peaks, setPeaks] = useState<number[]>([]);
  const { preferences: { volume, muted } } = useAudioPreferences();
  useEffect(() => {
    const element=media.current;if(!element)return;
    if(preview.current){element.volume=1;element.muted=false;updatePreview(preview.current,gainDb??0,volume,muted);}
    else{element.volume=volume;element.muted=muted;}
  }, [volume, muted,gainDb]);
  useEffect(()=>{const element=media.current;return()=>{if(element){element.pause();disconnectPreview(element);}};},[]);
  const preparePreview=()=>{
    if(gainDb===undefined || !media.current)return Promise.resolve();
    const channel=connectPreview(media.current);preview.current=channel;
    media.current.volume=1;media.current.muted=false;updatePreview(channel,gainDb,volume,muted);
    return channel.context.resume();
  };
  useEffect(() => {
    setElapsed(0); setDuration(0); setPlaying(false); setLoading(true); setError(false);
  }, [src]);
  useEffect(() => {
    if(hideWave)return;
    setPeaks(peakCache.get(src) ?? []); setWaveformError(false);
    if (peakCache.has(src)) return;
    const controller = new AbortController();
    const decode = async () => {
      if (controller.signal.aborted) return;
      try {
        const response = await fetch(src, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]) });
        if (!response.ok) throw new Error('Waveform source unavailable');
        const bytes = await response.arrayBuffer();
        if (controller.signal.aborted) return;
        const context = new OfflineAudioContext(1, 1, 8000);
        const buffer = await context.decodeAudioData(bytes);
        if (controller.signal.aborted) return;
        const values = waveformPeaks(Array.from({ length: buffer.numberOfChannels }, (_, i) => buffer.getChannelData(i)));
        if (peakCache.size >= 20) peakCache.delete(peakCache.keys().next().value!);
        peakCache.set(src, values); setPeaks(values);
      } catch { if (!controller.signal.aborted) setWaveformError(true); }

    };
    waveformQueue = waveformQueue.then(decode, decode);
    return () => controller.abort();
  }, [src, waveformAttempt,hideWave]);
  const begin=range?.start??0,end=Math.min(duration,range?.end??duration),shownDuration=Math.max(0,end-begin);
  useEffect(()=>{const el=media.current;if(el && duration && (el.currentTime<begin || el.currentTime>end)){el.currentTime=begin;setElapsed(begin);onPosition?.(begin);}},[begin,end,duration]);
  const syncPosition=(el:HTMLAudioElement)=>{if(range && el.currentTime>=end){el.pause();el.currentTime=end;}setElapsed(el.currentTime);onPosition?.(el.currentTime);};
  const toggle = async () => {
    const element = media.current; if (!element) return;
    if (!element.paused) { element.pause(); return; }
    if (element.ended || element.currentTime>=end-.01 || element.currentTime<begin) element.currentTime = begin;
    setError(false);
    try { const ready=preparePreview();await Promise.all([ready,element.play()]); } catch (e) { if (!(e instanceof DOMException && e.name === 'AbortError')) { setError(true); setLoading(false); } }
  };
  const seek = (seconds: number) => { if (media.current && duration > 0) { media.current.currentTime = Math.max(begin,Math.min(end,seconds+begin)); setElapsed(media.current.currentTime); } };
  useEffect(() => {
    if (!playing) return;
    let frame = 0;
    const sync = () => { if (media.current) syncPosition(media.current); frame = requestAnimationFrame(sync); };
    frame = requestAnimationFrame(sync); return () => cancelAnimationFrame(frame);
  }, [playing,begin,end]);
  const progress = shownDuration > 0 ? Math.max(0, Math.min(1, (elapsed-begin) / shownDuration)) : 0;
  return <div className="audio-player" role="group" aria-label={label}>
    <div className="audio-player-main">
      <button type="button" className="round quiet audio-play" aria-label={`${t(error ? 'retryAudio' : playing ? 'pausePlayback' : 'play')} — ${label}`} disabled={loading && !error && !duration} onClick={() => error ? (setError(false), setLoading(true), media.current?.load()) : void toggle()}>{error ? <ArrowCounterClockwise size={20} /> : playing ? <Pause size={18} weight="fill" /> : <Play size={18} weight="fill" />}</button>
      {!hideWave && (peaks.length > 0 ? <SeekWave disabled={!duration || error} peaks={range?croppedPeaks(peaks,begin,end,duration):peaks} duration={shownDuration} progress={progress} label={`${t('seek')} — ${label}`} onSeek={seek} /> : <div className="waveform-status" role="status">{waveformError ? <button type="button" className="text-link" onClick={() => setWaveformAttempt(value => value + 1)}>{t('retryWaveform')}</button> : <span>{t('buildingWaveform')}</span>}</div>)}
      <span className="audio-time">{audioTime(Math.max(0,elapsed-begin))} <span>/ {audioTime(shownDuration)}</span></span>
      <VolumeControl locale={locale} label={label} />
      <Menu label={`${t('audioActions')} — ${label}`} icon={DotsThree} className="audio-actions"><p className="menu-label">{t('playbackSpeed')}</p>{[0.75, 1, 1.25, 1.5, 2].map(speed => <button type="button" key={speed} aria-pressed={rate === speed} onClick={() => setRate(speed)}><span>{speed}×</span>{rate === speed && <Check size={16} />}</button>)}<a href={downloadSrc??src} download={downloadName ?? `${label.replaceAll('/', '-').slice(0,100)}.wav`}><DownloadSimple size={18} />{gainDb===undefined?t('downloadRecording'):locale==='ru'?'Скачать исходную запись':'Download original recording'}</a></Menu>
    </div>
    {error ? <p className="generation-error" role="alert">{t('playbackError')}</p> : loading && <p className="audio-loading" role="status">{t('loadingAudio')}</p>}
    <audio ref={media} src={src} preload="metadata" aria-hidden="true" onPlay={event => { setPlaying(true); onPlay(event.currentTarget); }} onPause={() => setPlaying(false)} onEnded={() => { setPlaying(false); setElapsed(duration); }} onLoadedMetadata={event => { const value = event.currentTarget.duration; if (Number.isFinite(value) && value > 0) { setDuration(value); onDuration?.(value); setLoading(false);if(restorePlayback){const seconds=Math.max(0,Math.min(value,restorePlayback.seconds));event.currentTarget.currentTime=seconds;setElapsed(seconds);if(restorePlayback.playing)void event.currentTarget.play().catch(()=>setError(true));} } }} onCanPlay={() => setLoading(false)} onWaiting={() => setLoading(true)} onTimeUpdate={event => syncPosition(event.currentTarget)} onError={() => { setError(true); setPlaying(false); setLoading(false); }} />
  </div>;
}
