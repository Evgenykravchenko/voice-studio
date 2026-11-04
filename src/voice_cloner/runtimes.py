"""Reproducible optional runtimes, installed only below this project's .runtime."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

SPECS = {
    'mlx-audio': 'import mlx_audio.tts.utils, mlx_whisper, soundfile',
    'piper': "import os; from pathlib import Path; import piper; data=os.path.relpath(Path(piper.__file__).resolve().parent/'espeak-ng-data'); os.environ['ESPEAK_DATA_PATH']=data; from piper import PiperVoice; from piper.phonemize_espeak import EspeakPhonemizer; assert EspeakPhonemizer(data).phonemize('ru', 'Проверка.')",
    'mlx-audio-extended': 'import mlx_audio.tts.utils, mlx_audio.stt.utils, mlx_whisper, misaki.en, librosa',
    'cosyvoice': "from mlx_audio.tts.models.cosyvoice3.cosyvoice3 import Model; import fugashi, webrtcvad; assert not webrtcvad.Vad(1).is_speech(b'\\x00\\x00'*160,16000)",
    'f5': 'from f5_tts_mlx.cfm import F5TTS',
    'torch-audio': "import torch, torchaudio; from TTS.tts.models.xtts import Xtts; from transformers import AutoModel; from TTS.tts.layers.xtts.tokenizer import split_sentence, VoiceBpeTokenizer; assert len(split_sentence('Это проверка разделения предложений. '*12,'ru',182))>1; assert all(VoiceBpeTokenizer().preprocess_text(text,lang) for text,lang in [('こんにちは。','ja'),('首先检查录音。','zh')])",
    'parler': 'from parler_tts import ParlerTTSForConditionalGeneration',
    'index':'from mlx_indextts.generate_v2 import IndexTTSv2',
    'moss':'from transformers import AutoModel, AutoProcessor',
    'faster-whisper': 'from faster_whisper import WhisperModel',
}
PYTHON_VERSIONS = {name:'3.11.18' for name in ['cosyvoice','f5','torch-audio','parler','index','moss']}
BUILTIN = {'mlx-speech','mlx-whisper'}
PROBE_TIMEOUT = 180  # Cold Torch/Transformers imports also populate the private bytecode cache.


def python_for(runtime, root):
    if runtime in BUILTIN: return root / '.venv/bin/python'
    return root / '.runtime/engines' / runtime / 'bin/python'


def interpreter_local(runtime, root):
    """Reject moved venvs that still use another checkout's managed Python.

    QA may deliberately symlink an entire environment. Resolve that environment
    first, then check its owning project's Python, rather than following a stale
    interpreter link out of an otherwise copied environment.
    """
    binary=python_for(runtime,root);folder=binary.parent.parent.resolve()
    owner=folder.parent if runtime in BUILTIN else folder.parents[2]
    allowed=(folder,owner/'.runtime/python')
    try:
        executable=binary.resolve(strict=True)
        if not executable.is_file() or not any(executable.is_relative_to(p) for p in allowed):return False
        config=folder/'pyvenv.cfg'
        values=dict(line.split('=',1) for line in config.read_text().splitlines() if '=' in line)
        home=next((v.strip() for k,v in values.items() if k.strip()=='home'),None)
        if not home:return False
        home_path=Path(home)
        if not home_path.is_absolute():home_path=folder/home_path
        return any(home_path.resolve().is_relative_to(p) for p in allowed)
    except (OSError,ValueError,IndexError):return False


def recipes(root):
    path=root/'engines/sources.json'
    return json.loads(path.read_text()) if path.is_file() else {}


def signature(runtime, root):
    value=(root/'engines'/(runtime+'.lock')).read_bytes()
    source=recipes(root).get(runtime)
    if source:value+=json.dumps(source,sort_keys=True).encode()
    return hashlib.sha256(value).hexdigest()


def module_paths(runtime, root):
    paths=[root/'src',root/'vendor']
    source=recipes(root).get(runtime)
    if source:paths.append(root/'.runtime/sources'/source['directory'])
    return os.pathsep.join(str(path) for path in paths)


def prepare_source(runtime, root):
    source=recipes(root).get(runtime)
    if not source:return
    import urllib.request,urllib.error,tarfile,time
    archive=root/'.runtime/cache/sources'/(runtime+'.tar.gz')
    target=root/'.runtime/sources'/source['directory']
    def digest(path):
        with path.open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
    if not archive.is_file() or digest(archive)!=source['sha256']:
        archive.parent.mkdir(parents=True,exist_ok=True)
        temporary=archive.with_suffix('.part')
        # These pinned source archives are small; retry a failed transfer from the
        # beginning, retaining the last partial for diagnosis. Never extract it.
        for attempt in range(3):
            try:
                with urllib.request.urlopen(source['url'],timeout=300) as response, temporary.open('wb') as output:
                    shutil_copy(response,output)
                break
            except OSError as exc:
                if isinstance(exc,urllib.error.HTTPError) and exc.code<500 and exc.code!=429:raise
                if attempt==2:raise
                time.sleep(attempt+1)
        if digest(temporary)!=source['sha256']:
            temporary.unlink(missing_ok=True)
            raise ValueError('Проверка исходников адаптера не прошла.')
        temporary.replace(archive)
    destination=target.parent;destination.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive) as stream:stream.extractall(destination,filter='data')


def shutil_copy(source,target):
    import shutil
    shutil.copyfileobj(source,target)


def ready(runtime, root):
    if runtime not in SPECS:
        return runtime is None or (runtime in BUILTIN and interpreter_local(runtime,root))
    marker = root / '.runtime/engines' / runtime / 'ready.json'
    try:
        source=recipes(root).get(runtime)
        source_present=not source or (root/'.runtime/sources'/source['directory']).is_dir()
        return source_present and interpreter_local(runtime,root) and json.loads(marker.read_text())['lock'] == signature(runtime, root)
    except (OSError, ValueError, KeyError):
        return False


def environment(root):
    env = dict(os.environ)
    cache = root / '.runtime/cache'
    env['PATH']=str(root/'.runtime/bin')+os.pathsep+env.get('PATH','')
    env.update(UV_CACHE_DIR=str(cache / 'uv'), UV_PYTHON_INSTALL_DIR=str(root / '.runtime/python'), UV_PYTHON_BIN_DIR=str(root/'.runtime/bin'),
               XDG_CACHE_HOME=str(cache), HF_HOME=str(cache / 'huggingface'),
               HF_HUB_CACHE=str(cache / 'huggingface/hub'), HUGGINGFACE_HUB_CACHE=str(cache / 'huggingface/hub'),
               TORCH_HOME=str(cache / 'torch'), NUMBA_CACHE_DIR=str(cache / 'numba'),
               MPLCONFIGDIR=str(cache / 'matplotlib'), PYTHONPYCACHEPREFIX=str(root / '.runtime/pycache'),
               HF_HUB_DISABLE_TELEMETRY='1', HF_HUB_DISABLE_IMPLICIT_TOKEN='1', PIP_DISABLE_PIP_VERSION_CHECK='1')
    env.pop('PYTHONPATH', None)
    env.pop('VIRTUAL_ENV', None)
    env.setdefault('UV_HTTP_TIMEOUT', '300')
    env.setdefault('UV_HTTP_RETRIES', '5')
    return env


def install(runtime, root):
    if ready(runtime, root):
        return
    if runtime not in SPECS:
        raise ValueError('Эта модель пока не поддерживает установку из студии.')
    uv = root / '.runtime/bin/uv'
    if not uv.is_file():
        raise ValueError('Не найден локальный установщик uv. Повторите первоначальную установку проекта.')
    folder = python_for(runtime, root).parent.parent
    folder.parent.mkdir(parents=True, exist_ok=True)
    marker = folder / 'ready.json'
    marker.unlink(missing_ok=True)
    env = environment(root)
    prepare_source(runtime,root)
    env['PYTHONPATH']=module_paths(runtime,root)
    expected=signature(runtime,root)
    # stdout belongs to the catalog JSON protocol; installer output goes to its log.
    interpreter = PYTHON_VERSIONS.get(runtime, str(root / '.venv/bin/python'))
    command = [str(uv), 'venv', str(folder), '--allow-existing', '--relocatable', '--python', interpreter]
    if runtime in PYTHON_VERSIONS: command.append('--managed-python')
    subprocess.run(command, env=env, cwd=root, check=True, stdout=sys.stderr, stderr=sys.stderr, timeout=600)
    subprocess.run([str(uv), 'pip', 'sync', '--python', str(python_for(runtime, root)),
                    '--require-hashes', str(root / 'engines' / (runtime + '.lock'))],
                   env=env, cwd=root, check=True, stdout=sys.stderr, stderr=sys.stderr, timeout=3600)
    if runtime == 'cosyvoice':
        subprocess.run([str(uv),'pip','sync','--python',str(python_for(runtime,root)),'--require-hashes','--reinstall-package','mlx-audio-plus',str(root/'engines/cosyvoice.lock')],env=env,cwd=root,check=True,stdout=sys.stderr,stderr=sys.stderr,timeout=3600)
    subprocess.run([str(python_for(runtime, root)), '-c', SPECS[runtime]], env=env, cwd=root,
                   check=True, stdout=sys.stderr, stderr=sys.stderr, timeout=PROBE_TIMEOUT)
    temporary = marker.with_suffix('.tmp')
    if signature(runtime,root)!=expected:raise ValueError('Зависимости изменились во время установки. Повторите установку.')
    temporary.write_text(json.dumps({'lock': expected}))
    temporary.replace(marker)
