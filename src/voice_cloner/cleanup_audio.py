"""Bounded-memory speech restoration, retaining source timing and digital silence."""
from __future__ import annotations
import math
from pathlib import Path
import subprocess
import wave

RATE=44100

def retain_source_silence(source:Path,converted:Path):
    """Restore exact PCM silence after resampling, before neural processing can amplify ringing."""
    import numpy as np
    from .enhancement import silence_ranges
    try:
        with wave.open(str(source),'rb') as reader:
            source_rate=reader.getframerate()
        gaps=[(round(begin*RATE/source_rate),round(end*RATE/source_rate)) for begin,end in silence_ranges(source)]
    except (wave.Error,EOFError):
        return  # Compressed input has no exact PCM silence contract.
    if not gaps:return
    temporary=converted.with_suffix('.silence.wav')
    try:
        with wave.open(str(converted),'rb') as reader,wave.open(str(temporary),'wb') as writer:
            if reader.getframerate()!=RATE or reader.getnchannels()!=1 or reader.getsampwidth()!=2:
                raise ValueError('Некорректный формат подготовленной записи.')
            writer.setparams(reader.getparams());position=0;gap=0
            while data:=reader.readframes(RATE*8):
                samples=np.frombuffer(data,dtype='<i2').copy();end=position+len(samples)
                while gap<len(gaps) and gaps[gap][1]<=position:gap+=1
                current=gap
                while current<len(gaps) and gaps[current][0]<end:
                    begin,finish=gaps[current];samples[max(0,begin-position):min(len(samples),finish-position)]=0;current+=1
                writer.writeframesraw(samples.tobytes());position=end
        temporary.replace(converted)
    finally:temporary.unlink(missing_ok=True)

def restore_file(source:Path,before:Path,destination:Path,enhance,progress,*,hop_seconds=20,overlap_seconds=.25,context_seconds=.5):
    import numpy as np
    hop=max(1,round(hop_seconds*RATE));overlap=max(1,round(overlap_seconds*RATE));context=round(context_seconds*RATE)
    temporary=destination.with_suffix('.tmp')
    try:
        with wave.open(str(before),'rb') as reader,wave.open(str(temporary),'wb') as writer:
            total=reader.getnframes();writer.setparams((1,2,RATE,0,'NONE','not compressed'));tail=np.empty(0,dtype=np.float32)
            for part,start in enumerate(range(0,total,hop),1):
                progress(part,math.ceil(total/hop));read_start=max(0,start-context);read_end=min(total,start+hop+overlap+context)
                reader.setpos(read_start);audio=np.frombuffer(reader.readframes(read_end-read_start),dtype='<i2').astype(np.float32)/32768
                if np.max(np.abs(audio),initial=0)<1e-6:result=audio
                else:result=np.asarray(enhance(audio),dtype=np.float32).reshape(-1)
                if result.size!=audio.size or not np.isfinite(result).all():raise ValueError('Модель изменила длину фрагмента или вернула некорректный звук.')
                length=min(hop+overlap,total-start);offset=start-read_start;result=result[offset:offset+length].copy();original=audio[offset:offset+length]
                # Silence inserted by the editor stays silent, at exactly the same positions.
                zero=original==0;edges=np.flatnonzero(np.diff(np.r_[False,zero,False].astype(np.int8)))
                for begin,end in zip(edges[::2],edges[1::2]):
                    if end-begin>=round(.05*RATE):result[begin:end]=0
                blend=min(tail.size,result.size)
                if blend:
                    fade=np.linspace(0,1,blend,dtype=np.float32);result[:blend]=tail[:blend]*(1-fade)+result[:blend]*fade
                count=min(hop,result.size);writer.writeframesraw((np.clip(result[:count],-1,1)*32767).astype('<i2').tobytes());tail=result[count:]
        temporary.replace(destination)
    finally:temporary.unlink(missing_ok=True)

def process(model,job,root,emit):
    import torch
    from .models import snapshot
    from .cli import _ffmpeg_executable
    from resemble_enhance.enhancer.inference import enhance,denoise
    from .enhancement import finish,configuration,restored_path,denoised_path
    torch.set_num_threads(min(8,__import__('os').cpu_count() or 1));torch.manual_seed(job['seed'])
    folder=root/'data/studio/inputs'/job['sourceId'];before=folder/'before.wav';temporary=folder/'before.tmp.wav';config=configuration(job,root);output=restored_path(config,job,root);separate=(config.get('options') or {}).get('noiseReduction') is not None
    emit('progress',id=job['id'],stage='converting',part=0,total=0)
    if not before.is_file():
        try:
            ffmpeg=root/'.runtime/bin/ffmpeg'
            executable=str(ffmpeg) if ffmpeg.is_file() else _ffmpeg_executable()
            subprocess.run([executable,'-v','error','-nostdin','-y','-protocol_whitelist','file,pipe','-format_whitelist','wav,mp3,mov,flac,ogg,aac,aiff,matroska,webm','-i',str(folder/'source'),'-t','7201','-vn','-ac','1','-ar',str(RATE),'-c:a','pcm_s16le',str(temporary)],check=True,capture_output=True,timeout=600)
            with wave.open(str(temporary),'rb') as reader:
                duration=reader.getnframes()/RATE
                if duration<.08 or duration>7200:raise ValueError('Выберите запись длительностью от 0,08 секунды до двух часов.')
            retain_source_silence(folder/'source',temporary)
            temporary.replace(before)
        except subprocess.SubprocessError as exc:raise ValueError('Не удалось прочитать аудиофайл. Выберите поддерживаемую запись.') from exc
        finally:temporary.unlink(missing_ok=True)
    emit('progress',id=job['id'],stage='loading',part=0,total=0)
    path=snapshot(model)/'enhancer_stage2'
    def model_call(audio,cleanup=False):
        with torch.inference_mode():
            if cleanup:result,rate=denoise(torch.from_numpy(audio),RATE,'cpu',run_dir=path)
            else:result,rate=enhance(torch.from_numpy(audio),RATE,'cpu',nfe=32,run_dir=path,**({'lambd':0.} if separate else {}))
        if rate!=RATE:raise ValueError('Модель вернула неожиданную частоту дискретизации.')
        return result.cpu().numpy()
    output.parent.mkdir(parents=True,exist_ok=True)
    source=before
    if separate:
        source=denoised_path(config,job,root)
        if not source.is_file():restore_file(folder/'source',before,source,lambda a:model_call(a,True),lambda part,total:emit('progress',id=job['id'],stage='denoising',part=part,total=total))
    if not output.is_file():restore_file(folder/'source',source,output,lambda a:model_call(a),lambda part,total:emit('progress',id=job['id'],stage='restoring' if separate else 'cleaning',part=part,total=total))
    emit('progress',id=job['id'],stage='saving',part=1,total=1)
    return finish(job,root,emit)
