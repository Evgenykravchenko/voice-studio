"""Pinned, allowlisted model downloads. Inventory and selection never access the network or MLX."""
from __future__ import annotations

import argparse
import errno
import hashlib
import http.client
import json
import os
from pathlib import Path
import platform
import shutil
import ssl
import sys
import time

from .cli import PROJECT_DIR
from . import runtimes, model_resources

CATALOG = json.loads(Path(__file__).with_name('model-catalog.json').read_text())
INSTALLER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
DEFAULTS = {'synthesis': 'fish-s2-pro', 'transcription': 'whisper-small'}


def sha256_file(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def model_for(model_id):
    return next((model for model in CATALOG if model['id'] == model_id), None)


def synthesis_mode(model, job):
    default=model.get('synthesisMode','clone')
    mode=job.get('voiceMode') or default
    if mode not in model.get('synthesisModes',[default]):
        raise ValueError('Эта модель не поддерживает выбранный способ создания голоса.')
    return mode


def cache_dir(root=PROJECT_DIR):
    return root / '.runtime/cache/huggingface/hub'


def snapshot(model, root=PROJECT_DIR):
    if model.get('artifactSource') == 'url': return root / '.runtime/cache/artifacts' / model['id'] / model['revision']
    return cache_dir(root) / ('models--' + model['repo'].replace('/', '--')) / 'snapshots' / model['revision']


def file_path(model, file, root=PROJECT_DIR):
    if file.get('url'): return snapshot(model,root) / file['path']
    location = {'repo': file.get('repo', model['repo']), 'revision': file.get('revision', model['revision'])}
    return snapshot(location, root) / file['path']


def required_files(model,root=PROJECT_DIR):
    if not model.get('dynamicArtifact'):return model['files']
    try:
        record=json.loads((snapshot(model,root)/'manifest.json').read_text())
        file=dict(model['files'][0],size=record['size'],sha256=record['sha256'])
        if not isinstance(file['size'],int) or file['size']<1_000_000:return []
        return [file]
    except (OSError,ValueError,KeyError,TypeError):return []


def installed_bytes(model, root=PROJECT_DIR):
    return sum(file['size'] for file in required_files(model,root) if file_path(model, file, root).is_file() and file_path(model, file, root).stat().st_size == file['size'])


def validation_marker(model, root=PROJECT_DIR):
    return root / '.runtime/cache/model-validation' / (model['id'] + '.pending')


def installed(model, root=PROJECT_DIR):
    files=required_files(model,root)
    return bool(files) and not validation_marker(model,root).exists() and installed_bytes(model,root)==sum(file['size'] for file in files)


def ready(model, root=PROJECT_DIR):
    return model.get('integration', 'ready') == 'ready' and installed(model, root) and runtimes.ready(model.get('runtime'), root) and model_resources.ready(model, root)


def selections(root=PROJECT_DIR):
    result = dict(DEFAULTS)
    try:
        saved = json.loads((root / 'data/studio/models/selection.json').read_text())
        if not isinstance(saved, dict):
            return result
        for task in DEFAULTS:
            model = model_for(saved.get(task))
            if model and model['task'] == task and model.get('integration', 'ready') == 'ready':
                result[task] = model['id']
    except (OSError, ValueError, TypeError):
        pass
    return result


def selected_path(task, root=PROJECT_DIR):
    model = model_for(selections(root)[task])
    if not installed(model, root):
        raise ValueError(f"Сначала скачайте {model['name']} в разделе «Модели».")
    return str(snapshot(model, root) / model.get('artifactSubdir', ''))


def inventory(root=PROJECT_DIR):
    selected = selections(root)
    models = []
    for model in CATALOG:
        present = installed_bytes(model, root)
        models.append({key: value for key, value in model.items() if key != 'files'} | {
            'installed': installed(model, root), 'downloadedBytes': present,
            'sizeBytes': sum(f['size'] for f in required_files(model,root)) if model.get('dynamicArtifact') and required_files(model,root) else model['sizeBytes'],
            'runtimeReady': runtimes.ready(model.get('runtime'), root),
            'resourceReady': model_resources.ready(model, root),
            'ready': ready(model, root),
            'active': model.get('integration', 'ready') == 'ready' and selected.get(model['task']) == model['id'] and ready(model, root),
        })
    return {'models': models, 'supported': sys.platform == 'darwin' and platform.machine() == 'arm64',
            'freeBytes': shutil.disk_usage(root).free, 'platform': 'Apple Silicon'}


def select(model_id, root=PROJECT_DIR):
    model = model_for(model_id)
    if model and model['task'] not in DEFAULTS:
        raise ValueError('Откройте инструмент обработки в карточке модели.')
    if model and model.get('integration', 'ready') != 'ready':
        raise ValueError('Файлы модели можно скачать, но её движок ещё не подключён к студии.')
    if not model or not ready(model, root):
        raise ValueError('Выберите полностью установленную модель.')
    values = selections(root)
    values[model['task']] = model_id
    target = root / 'data/studio/models/selection.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(values))
    temporary.replace(target)


def report(**values):
    if 'stage' in values:
        values['installerSha256'] = INSTALLER_SHA256
    print(json.dumps(values), flush=True)


def transient_transfer_error(error):
    import urllib.error
    if isinstance(error, BrokenPipeError):
        return False  # The progress consumer closed; do not reopen the transfer.
    if isinstance(error, ssl.SSLCertVerificationError):
        return False
    if isinstance(error, urllib.error.HTTPError):
        return error.code in {408, 429, 500, 502, 503, 504}
    if isinstance(error, urllib.error.URLError):
        return isinstance(error.reason, BaseException) and transient_transfer_error(error.reason)
    # HTTP clients wrap certificate failures; never retry by weakening TLS checks.
    cause = error
    seen = set()
    while cause is not None and id(cause) not in seen:
        seen.add(id(cause))
        if isinstance(cause, ssl.SSLCertVerificationError):
            return False
        cause = cause.__cause__ or cause.__context__
    if isinstance(error, (TimeoutError, ConnectionError, http.client.IncompleteRead, ssl.SSLEOFError)):
        return True
    if isinstance(error, OSError) and error.errno in {
        errno.ECONNRESET, errno.ECONNABORTED, errno.ETIMEDOUT,
        errno.EPIPE, errno.ENETUNREACH, errno.EHOSTUNREACH,
    }:
        return True
    try:
        import httpx
    except ImportError:
        return False
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in {408, 429, 500, 502, 503, 504}
    return isinstance(error, (httpx.NetworkError, httpx.TimeoutException, httpx.RemoteProtocolError))


def retry_transfer(operation):
    for attempt in range(3):
        try:
            return operation()
        except Exception as error:
            if attempt == 2 or not transient_transfer_error(error):
                raise
            print(f'Transfer interrupted ({type(error).__name__}); retry {attempt + 2}/3.', file=sys.stderr, flush=True)
            time.sleep(2 ** attempt)


def direct_download(file, target, base, total, *, force=False):
    return retry_transfer(lambda: direct_download_once(file, target, base, total, force=force))


def direct_download_once(file, target, base, total, *, force=False):
    import urllib.request
    if target.is_file() and not force:return target
    target.parent.mkdir(parents=True,exist_ok=True)
    partial=target.with_suffix('.part')
    offset=partial.stat().st_size if partial.is_file() and not force else 0
    request=urllib.request.Request(file['url'],headers={'Range':f'bytes={offset}-'} if offset else {})
    with urllib.request.urlopen(request,timeout=60) as response:
        append=offset>0 and response.status==206
        if append and not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
            raise ValueError('Сервер вернул неверный диапазон файла. Повторите загрузку позже.')
        if not append:offset=0
        expected_length = response.headers.get('Content-Length')
        expected_end = offset + int(expected_length) if expected_length else file.get('size')
        with partial.open('ab' if append else 'wb') as output:
            while block:=response.read(1024*1024):
                output.write(block);offset+=len(block)
                if offset>(file.get('size') or 1_000_000_000):raise ValueError('Размер файла у автора изменился. Обновите каталог.')
                report(stage='downloading',downloadedBytes=base+offset,totalBytes=total)
        if expected_end is not None and offset < expected_end:
            raise ConnectionResetError(errno.ECONNRESET, 'Download ended before the complete response arrived')
    partial.replace(target)
    return target


def download_dynamic(model,root,*,prepare=True):
    import zipfile
    if shutil.disk_usage(root).free<1_600_000_000:raise ValueError('Освободите не менее 1,6 ГБ для установки.')
    marker=validation_marker(model,root);marker.parent.mkdir(parents=True,exist_ok=True);marker.touch()
    file=model['files'][0];target=file_path(model,file,root)
    report(stage='downloading',downloadedBytes=0,totalBytes=0)
    direct_download(file,target,0,0)
    report(stage='verifying',downloadedBytes=target.stat().st_size,totalBytes=target.stat().st_size)
    if target.stat().st_size<1_000_000 or not zipfile.is_zipfile(target):
        target.unlink(missing_ok=True);raise ValueError('Сервер автора вернул некорректный файл модели. Повторите установку позже.')
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:target.unlink(missing_ok=True);raise ValueError('Архив модели повреждён. Повторите загрузку.')
    digest=sha256_file(target)
    manifest=target.parent/'manifest.json';temporary=manifest.with_suffix('.tmp')
    temporary.write_text(json.dumps(dict(size=target.stat().st_size,sha256=digest)));temporary.replace(manifest)
    if prepare:
        report(stage='preparing',downloadedBytes=target.stat().st_size,totalBytes=target.stat().st_size)
        runtimes.install(model['runtime'],root)
    marker.unlink(missing_ok=True)
    report(stage='installed',downloadedBytes=target.stat().st_size,totalBytes=target.stat().st_size)


def download(model_id, root=PROJECT_DIR, *, prepare=True):
    model = model_for(model_id)
    if not model:
        raise ValueError('Неизвестная модель.')
    if not model.get('downloadable', True) or model.get('gated'):
        raise ValueError('Для этой модели используйте страницу автора: нужен отдельный доступ или способ установки.')
    if model.get('dynamicArtifact'):
        download_dynamic(model,root,prepare=prepare)
        return
    missing = model['sizeBytes'] - installed_bytes(model, root)
    reserve = 600_000_000 if model.get('integration') == 'ready' and not runtimes.ready(model.get('runtime'), root) else 100_000_000
    if not model_resources.ready(model, root):
        reserve += model.get('resourceBytes', 0)
    if missing > shutil.disk_usage(root).free - reserve:
        raise ValueError('Недостаточно места. Освободите место на диске и повторите скачивание.')
    # Force every cache into this project before importing the Hub; no user token is read.
    os.environ.update(HF_HOME=str(root / '.runtime/cache/huggingface'),
                      HF_HUB_CACHE=str(cache_dir(root)), HUGGINGFACE_HUB_CACHE=str(cache_dir(root)),
                      HF_HUB_DISABLE_TELEMETRY='1', HF_HUB_DISABLE_XET='1', HF_HUB_OFFLINE='0',
                      HF_HUB_DOWNLOAD_TIMEOUT='120', HF_HUB_ETAG_TIMEOUT='30')
    from huggingface_hub import hf_hub_download
    from tqdm.auto import tqdm
    marker = validation_marker(model, root)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    completed = 0
    for file in model['files']:
        file_size = file['size']
        base = completed
        class Progress(tqdm):
            def __init__(self, *args, **kwargs):
                kwargs['disable'] = False
                kwargs['file'] = sys.stderr
                self.last_report = 0
                super().__init__(*args, **kwargs)
            def update(self, n=1):
                value = super().update(n)
                if time.monotonic() - self.last_report > .25:
                    report(stage='downloading', downloadedBytes=min(model['sizeBytes'], base + int(self.n)), totalBytes=model['sizeBytes'])
                    self.last_report = time.monotonic()
                return value
        report(stage='downloading', downloadedBytes=completed, totalBytes=model['sizeBytes'])
        existing = file_path(model, file, root)
        force = existing.is_file() and existing.stat().st_size != file_size
        for attempt in range(2):
            if file.get('url'):
                target = direct_download(file,existing,base,model['sizeBytes'],force=force)
            else:
                target = Path(retry_transfer(lambda: hf_hub_download(
                    repo_id=file.get('repo', model['repo']), revision=file.get('revision', model['revision']), filename=file['path'],
                    cache_dir=cache_dir(root), token=False, tqdm_class=Progress, force_download=force)))
            correct = target.stat().st_size == file_size
            if correct and file.get('sha256'):
                report(stage='verifying', downloadedBytes=completed + file_size, totalBytes=model['sizeBytes'])
                with target.open('rb') as source:
                    correct = hashlib.file_digest(source, 'sha256').hexdigest() == file['sha256']
            if correct:
                break
            force = True
        else:
            raise ValueError('Проверка файлов модели не прошла. Повторите скачивание.')
        completed += file_size
    if installed_bytes(model, root) != model['sizeBytes']:
        raise ValueError('Не все файлы модели были скачаны.')
    if prepare and model.get('integration') == 'ready':
        report(stage='preparing', downloadedBytes=completed, totalBytes=completed)
        runtimes.install(model.get('runtime'), root)
        model_resources.prepare(model, root)
    marker.unlink(missing_ok=True)
    report(stage='installed', downloadedBytes=completed, totalBytes=completed)


def finish_import(model_id,root=PROJECT_DIR):
    model=model_for(model_id)
    if not model or not model.get('gated'):raise ValueError('Для этой модели импорт папки недоступен. Используйте установку из каталога.')
    stage=root/'data/studio/model-imports'/model_id
    marker=validation_marker(model,root);marker.parent.mkdir(parents=True,exist_ok=True);marker.touch()
    completed=0
    for file in model['files']:
        source=stage/file['path'];target=file_path(model,file,root)
        chosen=source if source.is_file() else target
        report(stage='verifying',downloadedBytes=completed,totalBytes=model['sizeBytes'])
        if not chosen.is_file() or chosen.stat().st_size!=file['size']:raise ValueError('В папке нет нужного файла: '+file['path'])
        if file.get('sha256') and sha256_file(chosen)!=file['sha256']:raise ValueError('Файл не соответствует выбранной версии модели: '+file['path'])
        if chosen==source:
            target.parent.mkdir(parents=True,exist_ok=True);source.replace(target)
        completed+=file['size']
    report(stage='preparing',downloadedBytes=completed,totalBytes=completed)
    runtimes.install(model['runtime'],root)
    marker.unlink(missing_ok=True)
    report(stage='installed',downloadedBytes=completed,totalBytes=completed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list', 'download', 'select', 'manifest', 'import'])
    parser.add_argument('model', nargs='?')
    parser.add_argument('--root', type=Path, default=PROJECT_DIR)
    args = parser.parse_args()
    try:
        if args.action == 'list':
            report(**inventory(args.root))
        elif args.action == 'manifest':
            model=model_for(args.model)
            if not model:raise ValueError('Неизвестная модель.')
            report(files=model['files'])
        elif args.action == 'import':
            finish_import(args.model,args.root)
        elif args.action == 'select':
            select(args.model, args.root)
            report(ok=True)
        else:
            download(args.model, args.root)
    except Exception as exc:
        message = str(exc) if isinstance(exc, ValueError) else 'Не удалось завершить установку. Проверьте интернет и свободное место, затем повторите. Скачанные файлы сохранятся.'
        print(str(exc), file=sys.stderr)
        report(stage='failed', error=message)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
