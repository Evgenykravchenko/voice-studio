#!/usr/bin/env python3
"""Real cloning tests at the supported reference-duration boundaries, in isolated data."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import models
from voice_cloner.cli import _ffmpeg_executable

spec=importlib.util.spec_from_file_location('inference_qa',ROOT/'scripts/verify-model-inference.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
SHORT={'en':'Hello. This is a clear and natural voice recording.',
       'ru':'Здравствуйте. Проверяем новую запись.'}
RATE=24000


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def canonical_source(language, app, directory):
    target=app/'data/profiles'/('qa-base-'+language)
    old=ROOT/'.runtime/release-audit/app/data/profiles'/('qa-'+language)
    expected=qa.EN_REFERENCE if language=='en' else qa.RU_REFERENCE
    if not target.exists() and (old/'profile.json').is_file():
        metadata=json.loads((old/'profile.json').read_text())
        if metadata.get('reference_text')==expected:
            shutil.copytree(old,target)
    if not (target/'profile.json').is_file():
        qa.fixture('kokoro' if language=='en' else 'piper-dmitri',expected,target.name,language,app,directory)
    return target/'reference.wav',expected


def short_source(language, app, directory):
    target=directory/('short-'+language+'.wav')
    if not target.is_file():
        cached=ROOT/'.runtime/release-audit/kokoro-presets.json'
        if language=='en' and cached.is_file():
            row=json.loads(cached.read_text())['cases']['af_alloy']
            source=cached.parent/row['audio']
            if row.get('status')=='passed' and row['job']['text']==SHORT[language] and digest(source)==row['metrics']['sha256']:
                shutil.copyfile(source,target)
        if not target.is_file():
            result=qa.generate(models.model_for('kokoro' if language=='en' else 'piper-dmitri'),SHORT[language],app,directory,language=language,case_id='short-'+language)
            shutil.copyfile(directory/result['audio'],target)
    return target,SHORT[language]


def pcm(source, directory, name):
    target=directory/(name+'-pcm.wav')
    subprocess.run([_ffmpeg_executable(),'-nostdin','-hide_banner','-loglevel','error','-y',
                    '-protocol_whitelist','file,pipe','-i',str(source),'-ac','1','-ar',str(RATE),
                    '-c:a','pcm_s16le',str(target)],check=True,capture_output=True,timeout=60)
    with wave.open(str(target),'rb') as reader:
        assert (reader.getnchannels(),reader.getsampwidth(),reader.getframerate())==(1,2,RATE)
        data=reader.readframes(reader.getnframes())
    return data


def profile(language, seconds, sources, app):
    folder=app/'data/profiles'/f'qa-boundary-{language}-{seconds}'
    folder.mkdir(exist_ok=True)
    audio=b'';texts=[];segments=[]
    # Only append complete utterances. Never cut audio and retain a longer transcript.
    for data,text,source in sources:
        while len(audio)+len(data)<=seconds*RATE*2:
            segments.append({'sourceSha256':digest(source),'startFrame':len(audio)//2,'frames':len(data)//2,'text':text})
            audio+=data;texts.append(text)
    if not texts:raise ValueError('No complete utterance fits the selected boundary')
    speech_frames=len(audio)//2
    audio+=b'\0'*(seconds*RATE*2-len(audio))
    with wave.open(str(folder/'reference.wav'),'wb') as writer:
        writer.setnchannels(1);writer.setsampwidth(2);writer.setframerate(RATE);writer.writeframes(audio)
    qa.atomic_json(folder/'profile.json',{'name':'QA boundary reference','reference_audio':'reference.wav',
                   'reference_text':' '.join(texts),'language':language,'clip_duration_seconds':seconds})
    qa.atomic_json(folder/'fixture.json',{'scope':'Anonymous synthetic utterances, complete segments and trailing silence; not a human similarity test',
                   'durationSeconds':seconds,'sampleRate':RATE,'speechFrames':speech_frames,'segments':segments})
    return folder


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    choose=parser.add_mutually_exclusive_group(required=True)
    choose.add_argument('--installed',action='store_true')
    choose.add_argument('--models',nargs='+')
    parser.add_argument('--limits',nargs='+',type=int,choices=[5,30],default=[5,30])
    parser.add_argument('--directory',type=Path,default=ROOT/'.runtime/release-audit/reference-boundaries')
    parser.add_argument('--runtime-root',type=Path,default=ROOT)
    parser.add_argument('--resources',action='store_true')
    parser.add_argument('--repeat',action='store_true')
    args=parser.parse_args()
    def cloning(m):return m and m['task']=='synthesis' and 'clone' in m.get('synthesisModes',[m.get('synthesisMode')])
    chosen=[m for m in models.CATALOG if cloning(m) and models.ready(m)] if args.installed else [models.model_for(x) for x in args.models]
    if any(not cloning(m) or not models.ready(m) for m in chosen):raise ValueError('Choose installed cloning models')
    directory=args.directory.resolve();app=qa.workspace(directory,runtime_root=args.runtime_root.resolve())
    qa.PROFILE_RESOURCES=args.resources
    for language in ['en','ru']:
        canonical,canonical_text=canonical_source(language,app,directory)
        short,short_text=short_source(language,app,directory)
        sources=[(pcm(canonical,directory,language+'-canonical'),canonical_text,canonical),
                 (pcm(short,directory,language+'-short'),short_text,short)]
        for seconds in args.limits:profile(language,seconds,sources,app)
    fingerprint=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'src/voice_cloner').glob('*.py')))
                              +(ROOT/'src/voice_cloner/model-catalog.json').read_bytes()+Path(__file__).read_bytes()).hexdigest()
    path=directory/'inference.json';report=json.loads(path.read_text()) if path.is_file() else {'scope':__doc__,'models':{}}
    report.update(runtimeRoot=str(args.runtime_root.resolve()),sourceFingerprint=fingerprint,
                  selectedModels=[m['id'] for m in chosen],excludedUnready=[m['id'] for m in models.CATALOG if cloning(m) and not models.ready(m)])
    for model in chosen:
        language='ru' if 'ru' in model['languages'] else 'en'
        reference_language=language if not model.get('referenceLanguages') or language in model['referenceLanguages'] else model['referenceLanguages'][0]
        for seconds in args.limits:
            case=f"{model['id']}-ref{seconds}";folder=app/'data/profiles'/f'qa-boundary-{reference_language}-{seconds}'
            before={name:digest(folder/name) for name in ['reference.wav','profile.json']}
            previous=report['models'].get(case,{})
            if previous.get('status')=='passed' and previous.get('sourceFingerprint')==fingerprint and previous.get('referenceHashes')==before and not args.repeat:continue
            row={'status':'running','sourceFingerprint':fingerprint,'referenceSeconds':seconds,'referenceHashes':before}
            report['models'][case]=row;qa.atomic_json(path,report);print(case,'starting',flush=True)
            try:
                row.update(qa.generate(model,qa.RU_TEXT if language=='ru' else qa.EN_TEXT,app,directory,
                                      language=language,voice=folder.name,voice_mode='clone',case_id=case))
                if before!={name:digest(folder/name) for name in before}:raise ValueError('Model modified its source profile')
                row['status']='passed'
            except Exception as exc:row.update(status='failed',error=str(exc))
            qa.atomic_json(path,report);print(case,row['status'],row.get('error') or row.get('seconds'),flush=True)
    return int(any(row['status']!='passed' for row in report['models'].values()))


if __name__=='__main__':raise SystemExit(main())
