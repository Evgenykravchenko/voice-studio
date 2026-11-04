#!/usr/bin/env python3
"""ASR screens completed preset audio for missing/wrong words; not a listening-quality verdict."""
import argparse
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unicodedata
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from voice_cloner import models, runtimes
spec=importlib.util.spec_from_file_location('inference_qa',ROOT/'scripts/verify-model-inference.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)


def normalized(text):
    text = unicodedata.normalize('NFC', text).casefold()
    return ''.join(c for c in text if unicodedata.category(c)[0] in 'LNM')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model')
    parser.add_argument('--asr', default='whisper-turbo')
    parser.add_argument('--directory',type=Path,default=ROOT/'.runtime/release-audit')
    parser.add_argument('--presets',nargs='*')
    args = parser.parse_args()
    folder = args.directory.resolve()
    cases = json.loads((folder / (args.model + '-presets.json')).read_text())['cases']
    asr = models.model_for(args.asr)
    if not asr or asr['task'] != 'transcription' or not models.ready(asr, ROOT):
        raise ValueError('An installed transcription model is required')
    os.environ.update(runtimes.environment(ROOT))
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    if asr['runtime']=='mlx-whisper':
        import mlx_whisper
        def transcribe(audio,language,preset):
            return mlx_whisper.transcribe(str(audio),path_or_hf_repo=str(models.snapshot(asr)),
                                         language=language,verbose=None,condition_on_previous_text=False)['text'].strip()
    else:
        logs=folder/'preset-transcript-reviews'/asr['id']/args.model
        app=qa.workspace(logs)
        def transcribe(audio,language,preset):
            job={'id':str(uuid.uuid4()),'type':'transcribe','modelId':asr['id'],'sourcePath':str(audio),'language':language}
            log=logs/(hashlib.sha256(preset.encode()).hexdigest()[:20]+'.log')
            events,_=qa.run([str(runtimes.python_for(asr['runtime'],app)),'-m','voice_cloner.runtime_worker'],job,asr['runtime'],app,log,900)
            terminal=next((e for e in reversed(events) if e.get('event') in ('completed','failed')), {})
            if terminal.get('event')!='completed' or not terminal.get('transcript'):
                raise ValueError(terminal.get('error') or 'ASR did not return a transcript')
            return terminal['transcript'].strip()
    output = folder / (args.model + '-preset-transcripts-' + asr['id'] + '.json')
    report = {'scope': 'ASR screening only; recognizer disagreement requires review, not automatic model failure',
              'asrModel': asr['id'], 'asrRevision': asr['revision'], 'cases': {}}
    prior_path=output if output.is_file() else folder/(args.model+'-preset-transcripts.json')
    if prior_path.is_file():
        prior = json.loads(prior_path.read_text())
        if prior.get('asrModel') == asr['id'] and prior.get('asrRevision') == asr['revision']:
            report = prior
    report['screenRule'] = 'exact-normalized-text-v2; every mismatch requires review'
    def save():
        temporary = output.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(output)
    for preset, row in cases.items():
        if args.presets and preset not in args.presets:continue
        if row.get('status') != 'passed':
            continue
        audio = (folder / row['audio']).resolve()
        if not audio.is_relative_to(folder):
            raise ValueError('QA audio must stay in its audit directory')
        digest = hashlib.sha256(audio.read_bytes()).hexdigest()
        previous = report['cases'].get(preset, {})
        if previous.get('sha256') == digest and previous.get('sourceFingerprint') == row.get('sourceFingerprint') and previous.get('transcript'):
            ratio = difflib.SequenceMatcher(None, normalized(row['job']['text']), normalized(previous['transcript']), autojunk=False).ratio()
            previous.update(expected=row['job']['text'], characterSimilarity=round(ratio, 4), status='screened' if ratio == 1 else 'review')
            save()
            continue
        result = {'sha256': digest, 'sourceFingerprint': row.get('sourceFingerprint'),
                  'language': row['language'], 'expected': row['job']['text']}
        try:
            # Select the fixture's language explicitly for both recognizers.
            heard = transcribe(audio,row['language'],preset)
            ratio = difflib.SequenceMatcher(None, normalized(row['job']['text']), normalized(heard), autojunk=False).ratio()
            result.update(transcript=heard, characterSimilarity=round(ratio, 4), status='screened' if ratio == 1 else 'review')
        except Exception as exc:
            result.update(status='error', error=str(exc))
        report['cases'][preset] = result
        save()
        print(preset, result['status'], result.get('characterSimilarity'), flush=True)
    return int(any(v['status'] == 'error' for v in report['cases'].values()))


if __name__ == '__main__':
    raise SystemExit(main())
