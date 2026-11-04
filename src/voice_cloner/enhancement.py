"""Deterministic mastering of a cached restoration; no model reload when tuning."""
from __future__ import annotations
import json
import math
from pathlib import Path
import re
import subprocess
import uuid
import wave

DEFAULTS=dict(noiseReduction=100,strength=30,clarity=20,warmth=0,deEss=35,leveling=True,protectPeaks=True)
RATE=44100

def options(value=None):
    result=DEFAULTS | (value or {})
    if result['noiseReduction'] is None:result['noiseReduction']=100
    for key,low,high in [('noiseReduction',0,100),('strength',0,100),('clarity',0,100),('warmth',-100,100),('deEss',0,100)]:
        if type(result[key]) not in (int,float) or not math.isfinite(result[key]) or not low<=result[key]<=high:raise ValueError('Некорректные настройки улучшения.')
    if any(type(result[k]) is not bool for k in ['leveling','protectPeaks']):raise ValueError('Некорректные настройки улучшения.')
    return result

def configuration(job,root):
    path=root/'data/studio/cleanups'/(str(uuid.UUID(job['id']))+'.json')
    return json.loads(path.read_text()) if path.is_file() else {}

def restored_path(config,job,root):
    base=str(uuid.UUID(config.get('baseId') or job['id']))
    separate=(config.get('options') or {}).get('noiseReduction') is not None
    path=root/'outputs/studio'/(base+('.natural-restored.wav' if separate else '.restored.wav'))
    if not separate and not path.is_file() and base!=job['id']:
        # Versions from before mastering was introduced contain the unmastered model output.
        original=root/'data/studio/cleanups'/(base+'.json')
        if original.is_file() and not json.loads(original.read_text()).get('options'):path=root/'outputs/studio'/(base+'.wav')
    return path

def denoised_path(config,job,root):
    return root/'outputs/studio'/(str(uuid.UUID(config.get('baseId') or job['id']))+'.denoised.wav')

def cached(job,root):
    config=configuration(job,root)
    return bool(config) and restored_path(config,job,root).is_file() and ((config.get('options') or {}).get('noiseReduction') is None or denoised_path(config,job,root).is_file())

def ffmpeg(root):
    file=root/'.runtime/bin/ffmpeg'
    if file.is_file():return str(file)
    from .cli import _ffmpeg_executable
    return _ffmpeg_executable()

def run(root,args):
    result=subprocess.run([ffmpeg(root),'-hide_banner','-nostdin','-y',*args],capture_output=True,text=True,timeout=1800)
    if result.returncode:raise ValueError('Не удалось обработать звук. Проверьте файл и повторите улучшение.')
    return result.stderr

def finite(value):
    try:number=float(value);return number if math.isfinite(number) else None
    except (ValueError,TypeError):return None

def measure(root,inputs,graph):
    log=run(root,[*inputs,'-filter_complex',graph+',astats=metadata=0:reset=0,loudnorm=I=-19:TP=-1:LRA=11:print_format=json[out]','-map','[out]','-f','null','-'])
    match=re.search(r'\{\s*"input_i".*?\}',log,re.S)
    if not match:raise ValueError('Не удалось измерить громкость записи.')
    data=json.loads(match.group());level=finite(data.get('input_i'))
    if level is None:
        rms=re.findall(r'RMS level dB:\s*([-+\w.]+)',log);level=finite(rms[-1]) if rms else None
    return dict(level=level,peak=finite(data.get('input_tp')))

def gain_to(level,target,maximum=18):
    return 0. if level is None else max(-36.,min(maximum,target-level))

def silence_ranges(path):
    import numpy as np
    result=[];start=None;position=0
    with wave.open(str(path),'rb') as reader:
        if reader.getsampwidth()!=2:return []
        rate=reader.getframerate();channels=reader.getnchannels()
        while data:=reader.readframes(rate*8):
            samples=np.frombuffer(data,dtype='<i2').reshape(-1,channels);zero=np.all(samples==0,axis=1)
            edges=np.flatnonzero(np.diff(np.r_[start is not None,zero].astype(np.int8)))
            for edge in edges:
                if zero[edge]:start=position+int(edge)
                elif start is not None:
                    if position+edge-start>=round(.05*rate):result.append((start,position+int(edge)))
                    start=None
            position+=len(samples)
    if start is not None and position-start>=round(.05*rate):result.append((start,position))
    return result

def retain_timing(source,processed,destination):
    import numpy as np
    gaps=silence_ranges(source);gap=0;position=0
    with wave.open(str(source),'rb') as original,wave.open(str(processed),'rb') as reader,wave.open(str(destination),'wb') as writer:
        frames=original.getnframes()
        if reader.getnframes()!=frames or reader.getframerate()!=RATE or reader.getsampwidth()!=2:raise ValueError('Обработка изменила длительность записи.')
        writer.setparams((1,2,RATE,0,'NONE','not compressed'))
        while data:=reader.readframes(RATE*8):
            samples=np.frombuffer(data,dtype='<i2').copy();end=position+len(samples)
            while gap<len(gaps) and gaps[gap][1]<=position:gap+=1
            current=gap
            while current<len(gaps) and gaps[current][0]<end:
                begin,finish=gaps[current];samples[max(0,begin-position):min(len(samples),finish-position)]=0;current+=1
            writer.writeframesraw(samples.tobytes());position=end

def finish(job,root,emit):
    config=configuration(job,root);settings=options(config.get('options'))
    folder=root/'data/studio/inputs'/str(uuid.UUID(job['sourceId']));before=folder/'before.wav';restored=restored_path(config,job,root)
    output=root/'outputs/studio'/(job['id']+'.wav');temporary=output.with_suffix('.mastering.wav');final=output.with_suffix('.final.wav')
    emit('progress',id=job['id'],stage='measuring',part=0,total=0)
    before_stats=measure(root,['-i',str(before)],'[0:a]anull')
    restored_stats=measure(root,['-i',str(restored)],'[0:a]anull')
    separate=(config.get('options') or {}).get('noiseReduction') is not None
    wet=settings['strength']/100
    if separate:
        denoised=denoised_path(config,job,root);clean_stats=measure(root,['-i',str(denoised)],'[0:a]anull');noise=settings['noiseReduction']/100
        alignment=0. if clean_stats['level'] is None or restored_stats['level'] is None else max(-18.,min(18.,clean_stats['level']-restored_stats['level']))
        # Keep the removed residual separate from voice reconstruction. At full cleanup the
        # original has coefficient zero at EVERY restoration strength, including zero.
        prefix=f'[0:a]volume={1-noise}[ambience];[1:a]volume={noise-wet}[natural];[2:a]volume={wet}*{10**(alignment/20):.10f}[restored];[ambience][natural][restored]amix=inputs=3:normalize=0:duration=first'
        inputs=['-i',str(before),'-i',str(denoised),'-i',str(restored)]
        reference=clean_stats if noise>=.5 else before_stats
    else:
        # Existing immutable versions keep their original mastering semantics.
        alignment=0. if before_stats['level'] is None or restored_stats['level'] is None else max(-18.,min(18.,before_stats['level']-restored_stats['level']))
        prefix=f'[0:a]volume={1-wet}[dry];[1:a]volume={wet}*{10**(alignment/20):.10f}[wet];[dry][wet]amix=inputs=2:normalize=0:duration=first'
        inputs=['-i',str(before),'-i',str(restored)];reference=before_stats
    filters=[]
    if settings['warmth']:filters.append(f"bass=f=200:width_type=q:w=.7:g={settings['warmth']*.04:.4f}")
    if settings['clarity']:filters.append(f"equalizer=f=3000:width_type=q:w=.8:g={settings['clarity']*.04:.4f}")
    if settings['deEss']:filters.append(f"deesser=i={settings['deEss']*.006:.4f}:m=.5:f=.5")
    if settings['leveling']:
        threshold=max(.001,min(.5,10**(((reference['level'] if reference['level'] is not None else -24))/20)))
        filters.append(f'acompressor=threshold={threshold:.8f}:ratio=2.5:attack=12:release=180:makeup=1:knee=2.828')
    graph=prefix+(','+','.join(filters) if filters else ',anull')
    try:
        emit('progress',id=job['id'],stage='mastering',part=0,total=0)
        filtered_stats=measure(root,inputs,graph)
        adjustment=gain_to(filtered_stats['level'],-19) if settings['leveling'] else 0.
        tail=f',volume={adjustment:.8f}dB'
        if settings['protectPeaks']:tail+=',alimiter=limit=0.891251:level=false:latency=true'
        with wave.open(str(before),'rb') as reader:frames=reader.getnframes()
        tail+=f',aresample={RATE},apad=whole_len={frames},atrim=end_sample={frames}[out]'
        run(root,[*inputs,'-filter_complex',graph+tail,'-map','[out]','-ar',str(RATE),'-ac','1','-c:a','pcm_s16le',str(temporary)])
        retain_timing(before,temporary,final)
        emit('progress',id=job['id'],stage='comparing',part=0,total=0)
        after_stats=measure(root,['-i',str(final)],'[0:a]anull')
        levels=[s['level'] for s in [before_stats,after_stats] if s['level'] is not None];target=min([-23.,*levels])
        comparison=[]
        for label,path,stats in [('before',before,before_stats),('after',final,after_stats)]:
            gain=gain_to(stats['level'],target,maximum=0)
            preview=output.with_suffix('.compare-'+label+'.wav');pending=preview.with_suffix('.tmp.wav')
            try:
                run(root,['-i',str(path),'-af',f'volume={gain:.8f}dB','-c:a','pcm_s16le',str(pending)]);pending.replace(preview)
            finally:pending.unlink(missing_ok=True)
            comparison.append(gain)
        metrics=dict(options=settings if separate else settings|dict(noiseReduction=None),pipeline='separate-noise-v2' if separate else 'legacy-blend-v1',before=before_stats,after=after_stats,comparisonGainDb=comparison)
        output.with_suffix('.analysis.json').write_text(json.dumps(metrics,allow_nan=False))
        final.replace(output)
        emit('progress',id=job['id'],stage='saving',part=1,total=1)
        return output
    finally:temporary.unlink(missing_ok=True);final.unlink(missing_ok=True)
