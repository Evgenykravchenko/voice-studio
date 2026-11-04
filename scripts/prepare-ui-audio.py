"""Prepare local demo clips and measured waveform peaks; no model calls or network."""
from pathlib import Path
import argparse
import array
import json
import wave

root = Path(__file__).resolve().parents[1]
target = root / 'frontend/public/audio'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', type=Path, help='Local PCM16 WAV recording longer than 43 seconds')
    source = parser.parse_args().audio.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f'Missing local test recording: {source}')
    target.mkdir(parents=True, exist_ok=True)
    manifest = []
    with wave.open(str(source), 'rb') as recording:
        params = recording.getparams()
        if params.sampwidth != 2:
            raise SystemExit('The demo recording must use signed 16-bit PCM.')
        data = recording.readframes(params.nframes)
        duration = params.nframes / params.framerate
        if duration <= 43:
            raise SystemExit('The demo recording must be longer than 43 seconds.')
        for number, (start, end) in enumerate([(0, 20), (20, 43), (43, duration)], 1):
            frame_size = params.sampwidth * params.nchannels
            part = data[int(start * params.framerate) * frame_size:int(end * params.framerate) * frame_size]
            filename = f'scene-{number}.wav'
            with wave.open(str(target / filename), 'wb') as clip:
                clip.setparams(params)
                clip.writeframes(part)
            samples = array.array('h', part)
            step = max(1, len(samples) // 360)
            peaks = [max(abs(s) for s in samples[i:i + step]) / 32768 for i in range(0, len(samples), step)][:360]
            manifest.append({'url': f'/audio/{filename}', 'duration': end - start, 'peaks': peaks})
    (root / 'frontend/src/audio-data.json').write_text(json.dumps(manifest), encoding='utf-8')
    print(f'Prepared {len(manifest)} local demo clips in {target}')

if __name__ == '__main__':
    main()
