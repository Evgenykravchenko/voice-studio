import { useEffect, useRef } from 'react';
import { audioTime as time } from './audio-utils';

export function Wave({ peaks, progress = 0 }: { peaks: number[]; progress?: number }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const progressRef = useRef(progress);
  const redraw = useRef<() => void>(() => {});
  useEffect(() => {
    const el = canvas.current; if (!el) return;
    const draw = () => {
      const width = el.clientWidth, height = el.clientHeight, dpr = devicePixelRatio || 1;
      el.width = width * dpr; el.height = height * dpr;
      const ctx = el.getContext('2d'); if (!ctx) return;
      ctx.scale(dpr, dpr);
      const style = getComputedStyle(el);
      const count = Math.min(peaks.length, Math.floor(width / 2));
      const bars = () => {
        for (let i = 0; i < count; i++) { const p = peaks[Math.floor(i * peaks.length / count)]; const h = Math.max(1, Math.pow(p, 0.65) * height); ctx.fillRect(i * width / count, (height - h) / 2, 1, h); }
      };
      ctx.fillStyle = style.getPropertyValue('--color-wave').trim(); bars();
      const played = Math.max(0, Math.min(1, progressRef.current));
      if (played > 0) {
        ctx.save(); ctx.beginPath(); ctx.rect(0, 0, width * played, height); ctx.clip();
        ctx.fillStyle = style.getPropertyValue('--color-accent').trim(); bars(); ctx.restore();
      }
    };
    redraw.current = draw;
    const resize = new ResizeObserver(draw); resize.observe(el); draw();
    const mutation = new MutationObserver(draw); mutation.observe(document.documentElement, { attributes: true, attributeFilter: ['data-mode'] });
    return () => { resize.disconnect(); mutation.disconnect(); redraw.current = () => {}; };
  }, [peaks]);
  useEffect(() => { progressRef.current = progress; redraw.current(); }, [progress]);
  return <canvas ref={canvas} className="wave" data-progress={progress.toFixed(4)} aria-hidden="true" />;
}

export function SeekWave({ peaks, progress, duration, label, onSeek, disabled = false }: { disabled?: boolean; peaks: number[]; progress: number; duration: number; label: string; onSeek: (seconds: number) => void }) {
  return <span className="wave-seek">
    <Wave peaks={peaks} progress={progress} />
    <input type="range" disabled={disabled} min={0} max={duration} step={0.1} value={progress * duration} aria-label={label} aria-valuetext={`${time(progress * duration)} / ${time(duration)}`} onChange={e => onSeek(Number(e.target.value))} />
  </span>;
}

