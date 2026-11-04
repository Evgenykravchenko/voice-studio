#!/usr/bin/env python3
"""Screen real generated audio with local ASR; not a perceptual or similarity verdict."""
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

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import models,runtimes
spec=importlib.util.spec_from_file_location('inference_qa',ROOT/'scripts/verify-model-inference.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFC',text).casefold() if unicodedata.category(c)[0] in 'LNM')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,default=ROOT/'.runtime/release-audit')
    parser.add_argument('--asr',default='whisper-turbo')
    parser.add_argument('--models',nargs='*')
    args=parser.parse_args();folder=args.directory.resolve()
    records=json.loads((folder/'inference.json').read_text())['models']
    asr=models.model_for(args.asr)
    if not asr or asr['task']!='transcription' or not models.ready(asr,ROOT):
        raise ValueError('Select an installed transcription model')
    os.environ.update(runtimes.environment(ROOT));os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    if asr['runtime']=='mlx-whisper':
        import mlx_whisper
        def transcribe(audio,language,name):
            return mlx_whisper.transcribe(str(audio),path_or_hf_repo=str(models.snapshot(asr)),language=None if language=='auto' else language,verbose=None,condition_on_previous_text=False)['text'].strip()
    else:
        logs=folder/'transcript-reviews'/asr['id'];app=qa.workspace(logs)
        def transcribe(audio,language,name):
            # Run each optional ASR in its own pinned runtime; never load a
            # second neural model alongside the recognizer in this process.
            job={'id':str(uuid.uuid4()),'type':'transcribe','modelId':asr['id'],'sourcePath':str(audio),'language':language}
            log=logs/(hashlib.sha256(name.encode()).hexdigest()[:20]+'.log')
            events,_=qa.run([str(runtimes.python_for(asr['runtime'],app)),'-m','voice_cloner.runtime_worker'],job,asr['runtime'],app,log,900)
            terminal=next((e for e in reversed(events) if e.get('event') in ['completed','failed']),{})
            if terminal.get('event')!='completed' or not terminal.get('transcript'):raise ValueError('ASR did not return a transcript')
            return terminal['transcript'].strip()
    output=folder/('model-transcripts-'+asr['id']+'.json')
    report={'scope':__doc__,'asrModel':asr['id'],'asrRevision':asr['revision'],'models':{}}
    if output.is_file():
        previous=json.loads(output.read_text())
        if previous.get('asrRevision')==asr['revision']:report=previous
    report['screenRule']='exact-normalized-text-v2; every mismatch requires review'
    for name,row in records.items():
        if args.models and name not in args.models:continue
        if row.get('status')!='passed' or not row.get('audio'):continue
        source_model=models.model_for(row['job'].get('modelId'))
        if source_model and source_model.get('adapter')=='moss-sfx':continue  # Sound effects contain no expected spoken transcript.
        audio=(folder/row['audio']).resolve()
        if not audio.is_relative_to(folder):raise ValueError('QA audio must stay in its audit directory')
        digest=hashlib.sha256(audio.read_bytes()).hexdigest()
        previous=report['models'].get(name,{})
        expected=row.get('expectedText') or row['job']['text'] or qa.EN_REFERENCE
        if previous.get('sha256')==digest and previous.get('transcript'):
            ratio=difflib.SequenceMatcher(None,normalized(expected),normalized(previous['transcript']),autojunk=False).ratio()
            previous.update(expected=expected,characterSimilarity=round(ratio,4),status='screened' if ratio==1 else 'review')
            qa.atomic_json(output,report)
            continue
        result={'sha256':digest,'sourceFingerprint':row['sourceFingerprint'],'expected':expected,'language':row['job']['language']}
        try:
            heard=transcribe(audio,result['language'],name)
            ratio=difflib.SequenceMatcher(None,normalized(expected),normalized(heard),autojunk=False).ratio()
            result.update(transcript=heard,characterSimilarity=round(ratio,4),status='screened' if ratio==1 else 'review')
        except Exception as exc:result.update(status='error',error=str(exc))
        report['models'][name]=result;qa.atomic_json(output,report)
        print(name,result['status'],result.get('characterSimilarity'),flush=True)
    return int(any(r['status']=='error' for r in report['models'].values()))


if __name__=='__main__':raise SystemExit(main())
