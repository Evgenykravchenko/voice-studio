"""Offline language resources bundled with pinned model artifacts."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile

from .cli import PROJECT_DIR

DICTIONARY_FILES = ('sys.dic', 'unk.dic', 'matrix.bin', 'char.bin', 'dicrc', 'mecabrc')


def bundle(model):
    return next((item for item in model['files'] if item.get('resource') == 'unidic'), None)


def location(model, root=PROJECT_DIR):
    resource = bundle(model)
    if resource is None:
        return None
    return root / '.runtime/cache/model-resources' / model['id'] / resource['sha256']


def dictionary(model, root=PROJECT_DIR):
    folder = location(model, root)
    if folder is None:
        return None
    try:
        record = json.loads((folder / 'prepared.json').read_text())
        if not isinstance(record, dict) or not isinstance(record.get('files'), dict) or not record['files']:
            return None
        relative = PurePosixPath(record['dictionary'])
        if relative.is_absolute() or '..' in relative.parts or record['archiveSha256'] != bundle(model)['sha256']:
            return None
        target = folder / relative
        if not all((target / name).is_file() for name in DICTIONARY_FILES):
            return None
        for name, size in record['files'].items():
            if not isinstance(size, int) or size < 0:
                return None
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or not (folder / path).is_file() or (folder / path).stat().st_size != size:
                return None
        return target
    except (OSError, ValueError, KeyError, TypeError):
        return None


def ready(model, root=PROJECT_DIR):
    return bundle(model) is None or dictionary(model, root) is not None


def prepare(model, root=PROJECT_DIR):
    resource = bundle(model)
    if resource is None or ready(model, root):
        return
    from .models import file_path, sha256_file
    archive_path = file_path(model, resource, root)
    if not archive_path.is_file() or sha256_file(archive_path) != resource['sha256']:
        raise ValueError('Словарь модели повреждён. Повторите установку модели.')
    target = location(model, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.dictionary-', dir=target.parent))
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            unpacked_size = sum(entry.file_size for entry in entries)
            if unpacked_size > 2_000_000_000 or unpacked_size + 100_000_000 > shutil.disk_usage(root).free:
                raise ValueError('Недостаточно места для словаря модели.')
            for entry in entries:
                name = PurePosixPath(entry.filename)
                if name.is_absolute() or '..' in name.parts or '\\' in entry.filename or stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError('Некорректный путь в архиве словаря.')
            archive.extractall(stage)
        candidates = list(stage.rglob('sys.dic'))
        if len(candidates) != 1:
            raise ValueError('В архиве отсутствует однозначный словарь UniDic.')
        chosen = candidates[0].parent
        (chosen / 'mecabrc').write_text('# Project-local UniDic configuration.\n')
        if not all((chosen / name).is_file() for name in DICTIONARY_FILES):
            raise ValueError('В архиве отсутствуют необходимые файлы словаря.')
        record = {'archiveSha256': resource['sha256'], 'dictionary': chosen.relative_to(stage).as_posix(),
                  'files': {path.relative_to(stage).as_posix(): path.stat().st_size for path in stage.rglob('*') if path.is_file()}}
        (stage / 'prepared.json').write_text(json.dumps(record))
        if target.exists():
            shutil.rmtree(target)
        stage.replace(target)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def initialize_kokoro(voice, model, preset):
    """Construct the cached pipeline with bounded native dictionary paths."""
    if preset.startswith('j'):
        initialize_japanese(voice, model)
    elif preset[0] in 'abefhip':
        import os
        from unittest.mock import patch
        from phonemizer.backend.espeak.api import EspeakAPI
        original = EspeakAPI.__init__
        # Phonemizer resolves the path before passing it to eSpeak. Its C path
        # buffer can reject a valid, deeply nested installation and terminate the
        # process. Shorten only that native argument, after the wrapper's checks.
        def initialize(instance, library, data_path):
            relative = os.path.relpath(Path(data_path).resolve()) if data_path is not None else None
            original(instance, library, relative)
        with patch.object(EspeakAPI, '__init__', initialize):
            voice._get_pipeline(preset[0])


def initialize_japanese(voice, model):
    """Only the bounded child sees this override; site-packages remains untouched."""
    from unittest.mock import patch
    from misaki import cutlet
    import fugashi
    path = dictionary(model)
    if path is None:
        raise ValueError('Для японских голосов нужен словарь. Повторите установку Kokoro в разделе «Модели».')
    # Fugashi/MeCab parses double-quoted paths, including project folders with spaces.
    def quoted(value):
        return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'
    options = '-r ' + quoted(path / 'mecabrc') + ' -d ' + quoted(path)
    with patch.object(cutlet, 'Tagger', lambda: fugashi.Tagger(options)):
        voice._get_pipeline('j')
