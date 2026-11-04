"""One isolated inference process per job; exits to release all optional-runtime memory."""
from __future__ import annotations
import contextlib
import json
from pathlib import Path
import re
import sys
import traceback
import wave

from .cli import PROJECT_DIR, _load_profile
from .models import model_for, ready, snapshot, file_path, synthesis_mode
from .worker import audio_info, script_parts

PROTOCOL = sys.stdout


def emit(event, **values):
    PROTOCOL.write(json.dumps({'event': event, **values}, ensure_ascii=False) + '\n')
    PROTOCOL.flush()


def generate(job):
    import numpy as np
    model = model_for(job['modelId'])
    if not model or not ready(model):
        raise ValueError('Выбранная модель не установлена. Откройте раздел «Модели».')
    if model.get('adapter')=='enhance' and (PROJECT_DIR/'data/studio/inputs'/str(job.get('sourceId'))/'cleanup.json').is_file():
        from .cleanup_audio import process as cleanup
        output=cleanup(model,job,PROJECT_DIR,emit)
        emit('completed',id=job['id'],seed=job['seed'],temperature=None,**audio_info(output))
        return
    if model.get('adapter') in ('openvoice','enhance'):
        from .processing import process
        emit('progress',id=job['id'],stage='generating')
        rate,audio=process(model,job)
        save_audio(job,audio,rate)
        return
    text=job['text'].strip()
    ssml=model.get('markup')=='ssml' and text.startswith('<speak')
    if ssml:
        from xml.etree.ElementTree import fromstring, ParseError
        try:
            if fromstring(text).tag!='speak':raise ValueError('SSML должен начинаться с <speak>.')
        except ParseError as exc:raise ValueError('Проверьте закрывающие теги SSML.') from exc
    parts = [(text,0)] if ssml or model.get('adapter')=='moss-sfx' else script_parts(text)
    if model.get('markup','plain') == 'plain' and any(re.search(r'\[[^]]*\]', speech) for speech, _ in parts):
        raise ValueError('Эта модель не поддерживает теги в квадратных скобках. Уберите теги эмоций; [pause:0.5] можно оставить.')
    mode = synthesis_mode(model,job)
    profile, reference = _load_profile(job['voiceId']) if mode == 'clone' else (None, None)
    if profile and model.get('referenceLanguages'):
        reference_language=profile.get('language','auto')
        if (reference_language!='auto' and reference_language not in model['referenceLanguages']) or re.search(r'[А-Яа-яЁё]',profile['reference_text']):
            raise ValueError('Для F5-TTS нужен образец на английском или китайском языке. Создайте отдельный профиль в разделе «Голоса».')
    preset = job.get('presetVoice') or (model.get('presetVoices') or [None])[0]
    if mode == 'preset' and preset not in model['presetVoices']:
        raise ValueError('Выберите готовый голос из списка.')
    if mode == 'design' and not str(job.get('voiceDescription') or '').strip():
        raise ValueError('Опишите голос, который нужно создать.')
    if mode == 'design' and model.get('adapter')=='omnivoice':
        from .rowwise import voice_instruction
        voice_instruction(job['voiceDescription'],text)
    if mode == 'design' and model.get('adapter')=='spark':
        from .voice_design import spark_options
        spark_options(job['voiceDescription'])
    emit('progress', id=job['id'], stage='loading', part=0, total=len(parts))
    from .synthesis import load
    from .local_resources import local_resources
    chunks = []
    with local_resources(model):
        rate, synthesize = load(model,job,reference,profile)
        for number,(speech,pause) in enumerate(parts,1):
            emit('progress', id=job['id'], stage='generating', part=number, total=len(parts))
            if speech:
                samples = []
                for value in synthesize(speech):
                    value = np.asarray(value,dtype=np.float32).squeeze()
                    if value.ndim==2: value=value.mean(axis=-1) if value.shape[-1]<=8 else value.mean(axis=0)
                    if value.ndim!=1 or not value.size or not np.isfinite(value).all():
                        raise ValueError('Модель вернула пустой или некорректный звук.')
                    samples.append(value)
                if not samples: raise ValueError('Модель не создала аудио.')
                chunks.extend(samples)
            if pause: chunks.append(np.zeros(round(pause*rate),dtype=np.float32))
    emit('progress', id=job['id'], stage='saving', part=len(parts), total=len(parts))
    save_audio(job,np.concatenate(chunks),rate)


def save_audio(job,audio,rate):
    import numpy as np
    model=model_for(job['modelId'])
    audio=np.asarray(audio,dtype=np.float32)
    if not audio.size or not np.isfinite(audio).all():raise ValueError('Модель вернула некорректное аудио.')
    if model.get('adapter')=='moss-sfx':
        # The codec rounds to whole latent blocks. Honor the requested file
        # duration and soften only the generated tail before trimming/padding.
        target=round(float(job.get('durationSeconds') or 6)*rate)
        if not rate<=target<=30*rate:raise ValueError('Длительность эффекта должна быть от 1 до 30 секунд.')
        audio=audio[:target].copy()
        fade=min(len(audio),max(1,round(.005*rate)))
        audio[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)
        if len(audio)<target:audio=np.pad(audio,(0,target-len(audio)))
    output = PROJECT_DIR / 'outputs/studio' / (job['id'] + '.wav')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp')
    with wave.open(str(temporary), 'wb') as writer:
        writer.setnchannels(1); writer.setsampwidth(2); writer.setframerate(rate)
        writer.writeframes((np.clip(audio, -1, 1) * 32767).astype('<i2').tobytes())
    temporary.replace(output)
    emit('completed', id=job['id'], seed=job['seed'], temperature=model.get('defaultTemperature'), **audio_info(output))


def main():
    job = json.loads(sys.stdin.readline())
    try:
        with contextlib.redirect_stdout(sys.stderr):
            if job.get('type') == 'transcribe':
                from .transcription import transcribe
                model=model_for(job['modelId'])
                if not model or not ready(model):raise ValueError('Модель распознавания не установлена.')
                emit('progress',id=job['id'],stage='transcribing')
                transcript=transcribe(model,Path(job['sourcePath']),job.get('language','auto'))
                emit('completed',id=job['id'],transcript=transcript)
            else:
                generate(job)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        emit('failed', id=job.get('id'), error=str(exc))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
