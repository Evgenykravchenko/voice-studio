"""Offline ASR adapters shared by voice preparation and the model workbench."""
from pathlib import Path
import math


def load_local_gigaam(folder):
    """Load the pinned author's module without scanning unused long-form VAD imports.

    Transformers' dynamic-module checker treats imports inside the optional VAD
    function as mandatory. Our short-utterance adapter never invokes that path.
    The source remains the hash-verified catalog file, and all weights stay offline.
    """
    import importlib.util
    import sys
    name = 'modeling_gigaam'
    specification = importlib.util.spec_from_file_location(name, folder / (name + '.py'))
    if specification is None or specification.loader is None:
        raise ValueError('Не найден локальный адаптер GigaAM. Повторите установку модели.')
    module = importlib.util.module_from_spec(specification)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
        config = module.GigaAMConfig.from_pretrained(str(folder), local_files_only=True)
        return module.GigaAMModel.from_pretrained(str(folder), config=config, local_files_only=True)
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise


def read_audio(path, rate=16000):
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    audio, original = sf.read(str(path),dtype='float32',always_2d=True)
    audio=audio.mean(axis=1)
    if original!=rate:
        divisor=math.gcd(original,rate)
        audio=resample_poly(audio,rate//divisor,original//divisor)
    return np.asarray(audio,dtype=np.float32)


def transcribe(model, path, language='auto'):
    validate_language(model, language)
    from .models import snapshot
    from .local_resources import local_resources
    folder=snapshot(model)/model.get('artifactSubdir','')
    with local_resources(model):
        adapter=model.get('adapter')
        if model['runtime']=='mlx-whisper':
            import mlx_whisper
            return mlx_whisper.transcribe(str(path),path_or_hf_repo=str(folder),language=None if language=='auto' else language,verbose=None)['text'].strip()
        if adapter=='faster-whisper':
            from faster_whisper import WhisperModel
            voice=WhisperModel(str(folder),device='cpu',compute_type='int8',local_files_only=True)
            # The workbench already canonicalizes input to PCM. Use the shared
            # mono/16 kHz loader, avoiding version-specific PyAV file arguments.
            segments,_=voice.transcribe(read_audio(path),language=None if language=='auto' else language)
            return ' '.join(segment.text.strip() for segment in segments).strip()
        if adapter=='gigaam':
            import torch
            # Only the reviewed, pinned official HF source in this bundle can be executed.
            voice=load_local_gigaam(folder).eval()
            audio=read_audio(path)
            # The upstream short-utterance contract is 25 seconds; never request gated VAD.
            pieces=[]
            import tempfile,soundfile as sf
            with tempfile.TemporaryDirectory(dir=folder.parents[2]) as temporary:
                for i in range(0,len(audio),20*16000):
                    target=Path(temporary)/'segment.wav';sf.write(target,audio[i:i+20*16000],16000)
                    with torch.inference_mode():pieces.append(voice.transcribe(str(target)))
            return ' '.join(pieces).strip()
        import mlx.core as mx
        from mlx_audio.stt.utils import load_model
        # Pinned Hub snapshots are named by commit hashes; do not infer the
        # architecture from that folder name when the source config omits it.
        voice=load_model(str(folder),model_type={'parakeet':'parakeet','qwen-asr':'qwen3_asr'}[adapter])
        kwargs={}
        if adapter=='qwen-asr' and language!='auto':
            from .synthesis import LANGUAGES
            kwargs['language']=LANGUAGES.get(language,language)
        result=voice.generate(mx.array(read_audio(path)),**kwargs)
        return result.text.strip()


def validate_language(model, language):
    supported = model.get('languages')
    if language != 'auto' and supported is not None and language not in supported:
        raise ValueError('Выбранная модель распознавания не поддерживает язык записи. Выберите другую модель в разделе «Модели».')
