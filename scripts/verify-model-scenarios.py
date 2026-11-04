#!/usr/bin/env python3
"""Real long-text/chunk/pause checks; speech quality requires separate transcript/listening review."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from voice_cloner import models
from voice_cloner.worker import script_parts

spec = importlib.util.spec_from_file_location('inference_qa', ROOT / 'scripts/verify-model-inference.py')
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)

ENGLISH = (
    'Today we are putting together a short lesson about a small software project. '
    'First, we describe the problem in plain language and decide what the application should do. '
    'Then we separate the user interface, the main rules, and the part that stores the data. '
    'Each part has a clear purpose, so a change to one screen does not force us to rewrite everything. '
    'Before adding another feature, we check the existing behavior and save a working version. '
    'This makes mistakes easier to find and gives us a safe place to return to. '
    '[pause:1.25] '
    'After this pause, we continue the lesson. We run the project again, read the result carefully, '
    'and make sure that every sentence remains in the recording. The lesson is now complete.'
)
RUSSIAN = (
    'Сегодня мы собираем небольшой урок о том, как устроен простой проект. '
    'Сначала описываем задачу обычными словами и решаем, что должно делать приложение. '
    'Затем отдельно рассматриваем интерфейс, основные правила и работу с данными. '
    'У каждой части есть понятная задача, поэтому изменение одного экрана не требует переписывать всё сразу. '
    'Перед добавлением новой возможности мы проверяем прежнее поведение и сохраняем рабочую версию. '
    'Так ошибку проще найти, а к удачному результату всегда можно вернуться. '
    '[pause:1.25] '
    'После этой паузы продолжаем урок. Снова запускаем проект, внимательно читаем результат '
    'и убеждаемся, что каждое предложение осталось в записи. Теперь наш урок завершён.'
)
PARLER_STYLE = ('A woman reads clearly at a steady pace, with moderate pitch and an expressive delivery. '
                'The audio is dry, close, and free of background noise.')


def silence_check(path: Path, minimum: float) -> dict:
    import numpy as np
    with wave.open(str(path), 'rb') as reader:
        rate = reader.getframerate()
        samples = np.frombuffer(reader.readframes(reader.getnframes()), dtype='<i2')
    edges = np.flatnonzero(np.diff(np.r_[False, samples == 0, False].astype(np.int8)))
    lengths = edges[1::2] - edges[::2]
    longest = int(lengths.max(initial=0))
    if longest < round(minimum * rate):
        raise ValueError('The requested pause is missing from the PCM output')
    return dict(requestedSeconds=minimum, longestZeroRunFrames=longest, sampleRate=rate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--installed', action='store_true', help='Only currently ready synthesis models; list exclusions')
    choice.add_argument('--models', nargs='+')
    parser.add_argument('--directory', type=Path, default=ROOT / '.runtime/release-audit/long-scenarios')
    parser.add_argument('--runtime-root', type=Path, default=ROOT)
    parser.add_argument('--repeat', action='store_true')
    args = parser.parse_args()
    chosen = ([m for m in models.CATALOG if m['task'] == 'synthesis' and models.ready(m, ROOT)]
              if args.installed else [models.model_for(name) for name in args.models])
    if any(m is None or m['task'] != 'synthesis' for m in chosen):
        raise ValueError('Choose catalog synthesis models')
    folder = args.directory.resolve()
    app = qa.workspace(folder, runtime_root=args.runtime_root.resolve())
    qa.fixture('kokoro', qa.EN_REFERENCE, 'qa-en', 'en', app, folder)
    qa.fixture('piper-dmitri', qa.RU_REFERENCE, 'qa-ru', 'ru', app, folder)
    path = folder / 'inference.json'
    report = json.loads(path.read_text()) if path.is_file() else dict(scope=__doc__, models={})
    fingerprint = hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT / 'src/voice_cloner').glob('*.py')))
                                + (ROOT / 'src/voice_cloner/model-catalog.json').read_bytes()
                                + Path(__file__).read_bytes()).hexdigest()
    report.update(updatedAt=datetime.now(timezone.utc).isoformat(), selectedModels=[m['id'] for m in chosen],
                  runtimeRoot=str(args.runtime_root.resolve()), sourceFingerprint=fingerprint,
                  excludedUnready=[m['id'] for m in models.CATALOG if m['task'] == 'synthesis' and not models.ready(m, ROOT)])
    qa.atomic_json(path, report)
    for model in chosen:
        previous = report['models'].get(model['id'], {})
        if previous.get('status') == 'passed' and previous.get('sourceFingerprint') == fingerprint and not args.repeat:
            continue
        language = 'ru' if 'ru' in model['languages'] else 'en'
        text = RUSSIAN if language == 'ru' else ENGLISH
        parts = script_parts(text)
        assert len(parts) >= 3 and len(text.split('[pause:')[0]) > 400
        row = dict(status='running', sourceFingerprint=fingerprint,
                   expectedText=re.sub(r'\[pause:[^]]+\]', '', text), expectedParts=len(parts))
        report['models'][model['id']] = row
        qa.atomic_json(path, report)
        print(model['id'], 'starting', len(text), 'characters', len(parts), 'parts', flush=True)
        try:
            row.update(qa.generate(model, text, app, folder, language=language,
                                  voice='qa-' + language if model.get('synthesisMode') == 'clone' else None,
                                  description=PARLER_STYLE if model['id'] == 'parler-mini' else None))
            if model.get('adapter') == 'xtts':
                row['nativeCharacterLimitExceeded'] = 'text length exceeds the character limit' in (folder / (model['id'] + '.log')).read_text().lower()
                if row['nativeCharacterLimitExceeded']:
                    raise ValueError('XTTS received text beyond its native language limit')
            row['pause'] = silence_check(folder / row['audio'], 1.25)
            row['status'] = 'passed'
        except Exception as exc:
            row.update(status='failed', error=str(exc))
        qa.atomic_json(path, report)
        print(model['id'], row['status'], row.get('error') or row.get('seconds'), flush=True)
    return int(any(row['status'] != 'passed' for row in report['models'].values()))


if __name__ == '__main__':
    raise SystemExit(main())
