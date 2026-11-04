"""Persistent local JSON-lines worker. Java owns HTTP, queuing and durable job metadata."""
from __future__ import annotations

import array
import contextlib
import gc
import json
import math
import os
from pathlib import Path
import re
import secrets
import subprocess
import selectors
import sys
import time
import traceback
import uuid
import wave

from .cli import PROJECT_DIR, _ensure_local_environment, _load_profile, _ffmpeg_executable
from .models import selected_path, model_for, selections, ready, snapshot
from . import runtimes

PROTOCOL = sys.stdout
PAUSE = re.compile(r"\[pause:(\d+(?:[.,]\d+)?)\]", re.IGNORECASE)
EMOTIONS = {"calm": "[neutral]", "excited": "[excited]", "whisper": "[whisper]", "laughing": "[laughing]", "angry": "[angry]"}
IDLE_SECONDS = 180


def emit(event: str, **values):
    PROTOCOL.write(json.dumps({"event": event, **values}, ensure_ascii=False) + "\n")
    PROTOCOL.flush()


def script_parts(text: str, limit: int = 400) -> list[tuple[str, float]]:
    """Application pause markers become PCM silence, never model speech tokens."""
    parts: list[tuple[str, float]] = []
    cursor = 0
    for marker in PAUSE.finditer(text):
        pause = float(marker.group(1).replace(',', '.'))
        if pause > 5:
            raise ValueError('Пауза должна быть от 0 до 5 секунд.')
        parts.append((text[cursor:marker.start()].strip(), pause))
        cursor = marker.end()
    parts.append((text[cursor:].strip(), 0))
    result = []
    for speech, pause in parts:
        if '[pause:' in speech.lower():
            raise ValueError('Неверная разметка паузы. Используйте [pause:0.5].')
        while len(speech) > limit:
            boundaries = list(re.finditer(r'(?<=[.!?])\s+|\n+', speech[:limit + 1]))
            cut = boundaries[-1].end() if boundaries else speech.rfind(' ', 0, limit)
            if cut <= 0:
                raise ValueError('Слишком длинное слово. Разделите текст на короткие предложения.')
            result.append((speech[:cut].strip(), 0.12))
            speech = speech[cut:].strip()
        result.append((speech, pause))
    if not any(re.sub(r'\[[^]]*\]', '', speech).strip() for speech, _ in result):
        raise ValueError('Добавьте произносимый текст, а не только теги или паузы.')
    return result


def audio_info(path: Path) -> dict:
    with wave.open(str(path), 'rb') as reader:
        if reader.getsampwidth() != 2:
            raise ValueError('Ожидался PCM16 WAV.')
        frames, rate = reader.getnframes(), reader.getframerate()
        if frames == 0:raise ValueError('Модель вернула пустую запись.')
        step=max(1,math.ceil(frames/360));peaks=[]
        while data:=reader.readframes(step):
            samples=array.array('h',data);peaks.append(round(max(abs(x) for x in samples)/32768,5))
    return {'duration': frames / rate, 'sampleRate': rate, 'peaks': peaks}


class Engine:
    def __init__(self):
        self.model = None
        self.references = {}
        self.last_used = time.monotonic()

    def unload(self):
        self.references.clear()
        self.model = None
        gc.collect()
        if 'mlx.core' in sys.modules:
            sys.modules['mlx.core'].clear_cache()
        emit('unloaded')

    def external(self, command, selected):
        env=runtimes.environment(PROJECT_DIR)
        env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONPATH=runtimes.module_paths(selected['runtime'],PROJECT_DIR))
        working=PROJECT_DIR/'.runtime/work'/selected['runtime'];working.mkdir(parents=True,exist_ok=True)
        with subprocess.Popen([str(runtimes.python_for(selected['runtime'],PROJECT_DIR)),'-u','-m','voice_cloner.runtime_worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=sys.stderr,text=True,env=env,cwd=working) as child:
            child.stdin.write(json.dumps(command)+'\n');child.stdin.close()
            terminal=None
            for line in child.stdout:
                event=json.loads(line)
                if event.get('event') in ('completed','failed'):terminal=event
                else:emit(event.pop('event'),**event)
            code=child.wait()
            if code or not terminal or terminal['event']!='completed':
                raise ValueError((terminal or {}).get('error','Модель не завершила обработку. Проверьте установку и повторите.'))
        return terminal

    def prepare_voice(self, job: dict):
        job_id = str(uuid.UUID(job['id']))
        directory = PROJECT_DIR / 'data/studio/voice-imports' / job_id
        source = directory / 'source'
        reference = directory / 'reference.wav'
        start, duration = float(job['start']), float(job['duration'])
        language = job.get('language', 'ru')
        if not math.isfinite(start) or not math.isfinite(duration) or start < 0 or start > 86400 or not 5 <= duration <= 30:
            raise ValueError('Выберите начало фрагмента и длительность от 5 до 30 секунд.')
        if not isinstance(language, str) or not re.fullmatch(r'auto|[a-z]{2,3}(?:-[A-Za-z0-9]+)?', language):
            raise ValueError('Выберите язык записи.')
        asr = model_for(job.get('modelId') or selections()['transcription'])
        if not asr or asr.get('task') != 'transcription' or not ready(asr): raise ValueError('Сначала установите модель распознавания.')
        from .transcription import validate_language
        validate_language(asr, language)
        # ASR and synthesis share this process/queue. Release Fish before loading Whisper.
        self.unload()
        emit('progress', id=job_id, stage='converting')
        try:
            subprocess.run([_ffmpeg_executable(), '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                '-protocol_whitelist', 'file,pipe', '-format_whitelist', 'wav,mp3,mov,flac,ogg,aac,aiff,matroska,webm', '-ss', str(start), '-i', str(source), '-t', str(duration),
                '-vn', '-ac', '1', '-ar', '44100', '-c:a', 'pcm_s16le', str(reference)],
                check=True, capture_output=True, timeout=60)
        except (subprocess.SubprocessError, OSError) as exc:
            raise ValueError('Не удалось прочитать запись. Выберите обычный аудиофайл и проверьте начало фрагмента.') from exc
        info = audio_info(reference)
        if info['duration'] < 5:
            raise ValueError('В выбранном фрагменте меньше 5 секунд. Выберите более раннее начало или другую запись.')
        with wave.open(str(reference), 'rb') as reader:
            samples = array.array('h', reader.readframes(reader.getnframes()))
        rms = math.sqrt(sum((sample / 32768) ** 2 for sample in samples) / len(samples))
        if rms < 0.002:
            raise ValueError('Запись слишком тихая или содержит тишину. Выберите фрагмент с отчётливой речью.')
        warnings = ['clipping'] if sum(abs(x) >= 32700 for x in samples) / len(samples) > 0.01 else []
        emit('progress', id=job_id, stage='transcribing')
        if asr['runtime'] == 'mlx-whisper':
            from .transcription import transcribe
            try:
                transcript=transcribe(asr,reference,language)
            finally:
                import importlib
                holder=getattr(importlib.import_module('mlx_whisper.transcribe'),'ModelHolder',None)
                if holder is not None:holder.model=None
                gc.collect()
                if 'mlx.core' in sys.modules:sys.modules['mlx.core'].clear_cache()
        else:
            result=self.external({'id':job_id,'type':'transcribe','modelId':asr['id'],'sourcePath':str(reference),'language':language},asr)
            transcript=result['transcript']
        if not transcript:raise ValueError('Не удалось распознать речь. Выберите запись с одним голосом без музыки.')
        self.last_used = time.monotonic()
        emit('completed', id=job_id, transcript=transcript, warnings=warnings, **info)

    def generate(self, job: dict):
        job_id = str(uuid.UUID(job['id']))
        profile_id = job['voiceId']
        text = job['text'].strip()
        if len(text)>3000 or (not text and not job.get('sourceId')):
            raise ValueError('Текст должен содержать от 1 до 3000 символов.')
        emotion = job.get('emotion', 'calm')
        if emotion not in EMOTIONS or not re.fullmatch(r'auto|[a-z]{2,3}(?:-[A-Za-z0-9]+)?', job.get('language', 'ru')):
            raise ValueError('Неизвестные настройки озвучки.')
        seed = job.get('seed')
        if seed is None:
            seed = secrets.randbits(32)
        if type(seed) is not int or not 0 <= seed <= 4294967295:
            raise ValueError('Seed должен быть целым числом от 0 до 4294967295.')
        model_id = job.get('modelId') or selections()['synthesis']
        selected = model_for(model_id)
        if model_id=='resemble-enhance':
            from .enhancement import cached,finish
            if cached(job,PROJECT_DIR):
                self.unload()
                output=finish(job,PROJECT_DIR,emit)
                emit('completed',id=job_id,seed=seed,temperature=None,**audio_info(output))
                self.last_used=time.monotonic()
                return
        if not selected or selected['task'] == 'transcription' or not ready(selected):
            raise ValueError('Сначала полностью установите выбранную модель в разделе «Модели».')
        if model_id != 'fish-s2-pro':
            self.unload()
            command = dict(job, modelId=model_id, seed=seed)
            terminal=self.external(command,selected)
            emit(terminal.pop('event'),**terminal)
            self.last_used = time.monotonic()
            return
        parts = script_parts(text)
        profile, reference_path = _load_profile(profile_id)
        import mlx.core as mx
        import mlx_speech
        import numpy as np

        if self.model is None:
            emit('progress', id=job_id, stage='loading', part=0, total=len(parts))
            # HF_HUB_OFFLINE prevents inference from downloading or sending anything.
            self.model = mlx_speech.tts.load(str(snapshot(selected)))
        emit('progress', id=job_id, stage='reference', part=0, total=len(parts))
        reference_key = (profile_id, reference_path.stat().st_mtime_ns, profile['reference_text'])
        if reference_key not in self.references:
            self.references[reference_key] = self.model.prepare_reference(str(reference_path), reference_text=profile['reference_text'])
        reference = self.references[reference_key]
        mx.random.seed(seed)
        chunks = []
        rate = 44100
        for number, (speech, pause) in enumerate(parts, 1):
            emit('progress', id=job_id, stage='generating', part=number, total=len(parts))
            if speech:
                prompt = speech if speech.startswith('[') else f'{EMOTIONS[emotion]} {speech}'
                # This pinned adapter has fixed sampling temperature (0.8).
                result = self.model.generate(prompt, reference_audio=reference, max_new_tokens=2048)
                rate = result.sample_rate
                samples = np.asarray(result.waveform, dtype=np.float32).reshape(-1)
                if not samples.size or not np.isfinite(samples).all():
                    raise ValueError('Модель вернула пустой или некорректный звук. Попробуйте другой текст или seed.')
                chunks.append(samples)
            if pause:
                chunks.append(np.zeros(round(pause * rate), dtype=np.float32))
            mx.clear_cache()
        emit('progress', id=job_id, stage='saving', part=len(parts), total=len(parts))
        audio = np.concatenate(chunks)
        output_dir = PROJECT_DIR / 'outputs' / 'studio'
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f'{job_id}.wav'
        temporary = output.with_suffix('.tmp')
        pcm = (np.clip(audio, -1, 1) * 32767).astype('<i2')
        with wave.open(str(temporary), 'wb') as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(rate)
            writer.writeframes(pcm.tobytes())
        temporary.replace(output)
        self.last_used = time.monotonic()
        emit('completed', id=job_id, seed=seed, temperature=0.8, **audio_info(output))


def main():
    cache = PROJECT_DIR / '.runtime' / 'cache'
    for key, value in {
        'XDG_CACHE_HOME': cache, 'HF_HOME': cache / 'huggingface',
        'HUGGINGFACE_HUB_CACHE': cache / 'huggingface' / 'hub',
        'TORCH_HOME': cache / 'torch', 'MPLCONFIGDIR': cache / 'matplotlib',
    }.items():
        os.environ[key] = str(value)
    _ensure_local_environment()
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    engine = Engine()
    selector = selectors.DefaultSelector()
    selector.register(sys.stdin, selectors.EVENT_READ)
    emit('ready')
    while True:
        events = selector.select(timeout=1)
        if not events:
            if engine.model is not None and time.monotonic() - engine.last_used >= IDLE_SECONDS:
                with contextlib.redirect_stdout(sys.stderr):
                    engine.unload()
            continue
        line = sys.stdin.readline()
        if not line:
            break
        job = {}
        try:
            job = json.loads(line)
            with contextlib.redirect_stdout(sys.stderr):
                if job.get("type") == "prepare_voice":
                    engine.prepare_voice(job)
                else:
                    engine.generate(job)
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            engine.last_used = time.monotonic()
            emit('failed', id=job.get('id'), error=str(exc))
    with contextlib.redirect_stdout(sys.stderr):
        engine.unload()


if __name__ == '__main__':
    main()
