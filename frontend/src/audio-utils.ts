export const audioTime = (seconds: number) => {
  const safe = Number.isFinite(seconds) ? Math.max(0, seconds) : 0;
  return `${Math.floor(safe / 60)}:${String(Math.floor(safe % 60)).padStart(2, '0')}`;
};

export function waveformPeaks(channels: Float32Array[], count = 240): number[] {
  const length = channels[0]?.length ?? 0;
  if (!length || count <= 0) return [];
  const step = Math.max(1, Math.ceil(length / count));
  const peaks: number[] = [];
  for (let start = 0; start < length; start += step) {
    let peak = 0;
    for (const channel of channels) {
      for (let i = start; i < Math.min(start + step, channel.length); i++) peak = Math.max(peak, Math.abs(channel[i]));
    }
    peaks.push(Math.min(1, peak));
  }
  return peaks;
}
