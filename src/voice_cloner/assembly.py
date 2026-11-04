"""Render an immutable, local project montage without loading a speech model."""
from __future__ import annotations
import array
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import wave

RATE = 48000

def run(command: list[str]) -> None:
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
    if result.returncode:
        raise ValueError('Audio processing failed: ' + result.stderr.decode(errors='replace')[-1200:])

def stats(path: Path) -> tuple[float, float]:
    energy = count = 0
    peak = 0
    with wave.open(str(path), 'rb') as audio:
        while data := audio.readframes(32768):
            values = array.array('h', data)
            if sys.byteorder != 'little': values.byteswap()
            energy += sum(v * v for v in values)
            count += len(values)
            peak = max(peak, max(map(abs, values), default=0))
    return math.sqrt(energy / max(count, 1)) / 32768, peak / 32768

def render(manifest: dict, directory: Path, root: Path) -> dict:
    ffmpeg = root / '.runtime/bin/ffmpeg'
    if not ffmpeg.is_file():
        import imageio_ffmpeg
        ffmpeg = Path(imageio_ffmpeg.get_ffmpeg_exe())
    clips = manifest['clips']
    if not clips or len(clips) > 500: raise ValueError('Choose 1–500 recorded scenes.')
    directory.mkdir(parents=True, exist_ok=True)
    total = 0
    spans = []
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        temp = Path(temporary)
        with wave.open(str(temp / 'master.wav'), 'wb') as master:
            master.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
            for index, clip in enumerate(clips):
                source = Path(clip['path']).resolve()
                if not any(source.is_relative_to((root / folder).resolve()) for folder in ('outputs/studio', 'frontend/public/audio')):
                    raise ValueError('Invalid audio source.')
                start, end, gap, gain = (float(clip[k]) for k in ('start', 'end', 'gap', 'gainDb'))
                if not all(map(math.isfinite, (start, end, gap, gain))) or not (0 <= start < end <= 7200 and end-start >= .08-1e-6 and 0 <= gap <= 5 and -18 <= gain <= 12):
                    raise ValueError('Invalid clip boundaries.')
                duration = end-start
                if total + duration + gap > 7200: raise ValueError('The assembled recording exceeds two hours.')
                raw = temp / 'raw.wav'
                run([str(ffmpeg), '-v', 'error', '-nostdin', '-y', '-i', str(source), '-ss', str(start), '-t', str(duration), '-ac', '1', '-ar', str(RATE), '-c:a', 'pcm_s16le', str(raw)])
                with wave.open(str(raw),'rb') as data:
                    actual = data.getnframes()/RATE
                if abs(actual-duration) > .04: raise ValueError('A source recording is shorter than its saved boundaries.')
                rms, peak = stats(raw)
                leveling = max(-6, min(6, 20 * math.log10(.1 / rms))) if manifest['leveling'] and rms > .0001 else 0
                # One static gain per scene preserves its own expressive dynamics.
                if manifest['leveling'] and peak: leveling = min(leveling, 20 * math.log10(.89 / peak))
                applied = leveling + gain
                filters = [f'volume={applied}dB']
                if manifest['softEdges']:
                    fade = min(.008, actual/4)
                    filters += [f'afade=t=in:d={fade}', f'afade=t=out:st={actual-fade}:d={fade}']
                filters += ['alimiter=limit=0.95:level=false:latency=true']
                processed = temp / 'clip.wav'
                run([str(ffmpeg), '-v', 'error', '-nostdin', '-y', '-i', str(raw), '-af', ','.join(filters), '-c:a', 'pcm_s16le', str(processed)])
                begin = total
                with wave.open(str(processed),'rb') as data:
                    frames = data.getnframes()
                    while chunk := data.readframes(32768): master.writeframesraw(chunk)
                total += frames / RATE
                spans.append({'sceneId':clip['sceneId'], 'sourceId':clip['sourceId'], 'start':begin, 'end':total, 'trimStart':start, 'trimEnd':end, 'appliedGainDb':round(applied,3)})
                silence = round(gap*RATE) if index < len(clips)-1 else 0
                while silence:
                    count = min(silence,32768); master.writeframesraw(b'\0' * count * 2); silence -= count
                if index < len(clips)-1: total += round(gap*RATE)/RATE
                print(json.dumps({'part':index+1,'total':len(clips)}),flush=True)
        run([str(ffmpeg), '-v','error','-nostdin','-y','-i',str(temp/'master.wav'),'-c:a','libmp3lame','-b:a','192k',str(temp/'master.mp3')])
        with wave.open(str(temp/'master.wav'),'rb') as audio:
            frames=audio.getnframes(); total=frames/RATE
            bucket=max(1,math.ceil(frames/720)); peaks=[]
            while chunk:=audio.readframes(bucket):
                values=array.array('h',chunk)
                if sys.byteorder!='little': values.byteswap()
                peaks.append(max(map(abs,values),default=0)/32768)
        os.replace(temp/'master.wav',directory/'master.wav')
        os.replace(temp/'master.mp3',directory/'master.mp3')
    result={'duration':total,'sampleRate':RATE,'peaks':peaks,'spans':spans}
    target=directory/'result.tmp'; target.write_text(json.dumps(result)); os.replace(target,directory/'result.json')
    return result

if __name__ == '__main__':
    manifest_path=Path(sys.argv[1]).resolve()
    root=Path.cwd().resolve()
    render(json.loads(manifest_path.read_text()),manifest_path.parent,root)
