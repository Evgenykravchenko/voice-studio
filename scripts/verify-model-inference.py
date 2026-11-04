#!/usr/bin/env python3
"""Serial real model smoke tests in isolated app data; opt-in downloads remain project-local.

Produces technical output evidence, not a subjective quality or release certificate.
Never changes the studio selection, user projects, profiles, jobs or original recordings.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import models,runtimes
EN_REFERENCE='Hello. I am speaking clearly and calmly in a quiet room. Today we are testing a local voice studio. Every sentence should sound natural and easy to understand.'
RU_REFERENCE='Здравствуйте. Это спокойная запись для проверки голосовой студии. Я говорю чётко и без спешки. Сегодня мы проверяем, как разные модели произносят обычные слова и соединяют предложения в понятную речь.'
EN_TEXT='Hello. This is a local voice test. The recording should be clear and easy to understand.'
RU_TEXT='Здравствуйте. Это проверка местной голосовой студии. Запись должна звучать ясно и естественно.'
PROFILE_RESOURCES=False
GENERATE_CODE='''import contextlib,json,sys
from voice_cloner.worker import Engine
with contextlib.redirect_stdout(sys.stderr): Engine().generate(json.loads(sys.stdin.readline()))
'''


def atomic_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(path)


def workspace(directory, *, runtime_root=ROOT):
    app=directory/'app';app.mkdir(parents=True,exist_ok=True)
    shutil.copytree(ROOT/'src',app/'src',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
    for name,target in [('engines',ROOT/'engines'),('vendor',ROOT/'vendor'),('.venv',runtime_root/'.venv'),('.runtime/engines',runtime_root/'.runtime/engines'),('.runtime/sources',runtime_root/'.runtime/sources'),('.runtime/cache',ROOT/'.runtime/cache')]:
        link=app/name;link.parent.mkdir(parents=True,exist_ok=True)
        if not link.exists() and not link.is_symlink():link.symlink_to(target,target_is_directory=True)
        if link.resolve()!=target.resolve():raise ValueError('Existing QA workspace uses another runtime/cache root')
    for name in ['uv','ffmpeg']:
        link=app/'.runtime/bin'/name;link.parent.mkdir(parents=True,exist_ok=True)
        if not link.exists() and not link.is_symlink():link.symlink_to(runtime_root/'.runtime/bin'/name)
    (app/'data/profiles').mkdir(parents=True,exist_ok=True)
    return app


def run(command,job,runtime,app,log,timeout,*,online=False):
    env=runtimes.environment(app)
    env.update(PYTHONPATH=runtimes.module_paths(runtime,app),HF_HUB_OFFLINE='0' if online else '1',TRANSFORMERS_OFFLINE='0' if online else '1',HF_HUB_DISABLE_IMPLICIT_TOKEN='1',HF_HUB_DISABLE_XET='1',OMP_NUM_THREADS='8')
    start=time.monotonic()
    if PROFILE_RESOURCES:
        if sys.platform!='darwin' or not Path('/usr/bin/time').is_file():
            raise ValueError('The resource collector requires macOS /usr/bin/time')
        command=['/usr/bin/time','-l',*command]
    with log.open('w') as stderr,log.with_suffix('.jsonl').open('w') as stdout:
        child=subprocess.Popen(command,cwd=app,env=env,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,text=True,start_new_session=True)
        try:
            child.communicate(json.dumps(job)+'\n' if job is not None else None,timeout=timeout)
        except (subprocess.TimeoutExpired,KeyboardInterrupt):
            os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise
    events=[]
    for line in log.with_suffix('.jsonl').read_text().splitlines():
        try:events.append(json.loads(line))
        except ValueError:pass
    if child.returncode:
        message=next((e.get('error') for e in reversed(events) if e.get('error')),None)
        raise RuntimeError(message or log.read_text()[-2000:])
    return events,round(time.monotonic()-start,2)


def resource_usage(log):
    import re
    found=re.findall(r'^\s*(\d+)\s+maximum resident set size\s*$',log.read_text(),re.MULTILINE)
    if not found:raise ValueError('macOS did not report maximum resident set size')
    return {'collector':'macos-time-l-maxrss-v1','maximumResidentSetBytes':int(found[-1]),
            'scope':'OS maximum RSS including waited-for descendants; not a simultaneous sum; excludes Java/browser'}


def audio_metrics(path):
    import array
    with wave.open(str(path),'rb') as reader:
        rate,frames,channels,width=reader.getframerate(),reader.getnframes(),reader.getnchannels(),reader.getsampwidth()
        if channels!=1 or width!=2 or not 8000<=rate<=192000 or not .1<=frames/rate<=180:
            raise ValueError('Unexpected output WAV format/duration')
        values=array.array('h',reader.readframes(frames))
    rms=math.sqrt(sum((v/32768)**2 for v in values)/len(values))
    if rms<.0001:raise ValueError('Output is effectively silent')
    return {'sampleRate':rate,'duration':frames/rate,'rmsDb':round(20*math.log10(rms),2),'clippedFraction':sum(abs(v)>=32760 for v in values)/len(values),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def artifact_state(model,app):
    return {str(models.file_path(model,item,app).relative_to(app)):
            (models.file_path(model,item,app).stat().st_size,models.file_path(model,item,app).stat().st_mtime_ns)
            for item in models.required_files(model,app)}


def generate(model,text,app,directory,*,language,voice=None,preset=None,case_id=None,voice_mode=None,description=None,emotion='calm'):
    before=artifact_state(model,app)
    mode=voice_mode or model.get('synthesisMode')
    job={'id':str(uuid.uuid4()),'modelId':model['id'],'text':text,'voiceId':voice,'voiceMode':voice_mode,'emotion':emotion,'language':language,'seed':42,'presetVoice':(model.get('presetVoices') or [None])[0],'voiceDescription':(description or 'A calm adult speaker with a natural conversational voice.') if mode=='design' else None}
    if preset is not None:job['presetVoice']=preset
    if model['task'] in ['conversion','processing']:
        source_id=str(uuid.uuid4());folder=app/'data/studio/inputs'/source_id;folder.mkdir(parents=True)
        shutil.copyfile(app/'data/profiles/qa-en/reference.wav',folder/'source')
        job.update(sourceId=source_id,text='',voiceId='qa-en')
    if model['adapter']=='moss-sfx':job.update(text='Gentle rain falling on a window.',durationSeconds=3)
    events,seconds=run([str(app/'.venv/bin/python'),'-u','-c',GENERATE_CODE],job,'mlx-speech',app,directory/((case_id or model['id'])+'.log'),900)
    terminal=next((e for e in reversed(events) if e.get('event') in ['completed','failed']),None)
    if not terminal or terminal['event']!='completed':raise ValueError('Worker did not emit successful completion')
    path=app/'outputs/studio'/(job['id']+'.wav')
    if before!=artifact_state(model,app) or not models.ready(model,app):
        raise ValueError('Inference modified pinned model files or made the model unavailable')
    metrics=audio_metrics(path)
    if model['adapter']=='moss-sfx' and abs(metrics['duration']-job['durationSeconds'])>1/metrics['sampleRate']:
        raise ValueError('Sound effect duration does not match the requested duration')
    result={'job':job,'seconds':seconds,'audio':str(path.relative_to(directory)),'metrics':metrics,'qualityReview':'pending','events':events}
    if PROFILE_RESOURCES:result['resources']=resource_usage(directory/((case_id or model['id'])+'.log'))
    return result


def fixture(model_id,text,profile_id,language,app,directory):
    folder=app/'data/profiles'/profile_id
    metadata=folder/'profile.json'
    if not metadata.is_file():
        result=generate(models.model_for(model_id),text,app,directory,language=language)
        folder.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(directory/result['audio'],folder/'reference.wav')
        atomic_json(metadata,{'name':'QA reference','reference_audio':'reference.wav','reference_text':text,'language':language})
    return folder/'reference.wav'


def main():
    global PROFILE_RESOURCES
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download',action='store_true',help='Explicitly install missing downloadable catalog entries')
    parser.add_argument('--models',nargs='*')
    parser.add_argument('--repeat',action='store_true',help='Run again even when the current source already passed')
    parser.add_argument('--resources',action='store_true',help='Record macOS maximum RSS for each real job (excludes Java/browser)')
    parser.add_argument('--directory',type=Path,default=ROOT/'.runtime/release-audit')
    parser.add_argument('--runtime-root',type=Path,default=ROOT,help='Use independently installed runtimes; weights remain in the verified shared model cache')
    args=parser.parse_args();PROFILE_RESOURCES=args.resources;directory=args.directory.resolve();directory.mkdir(parents=True,exist_ok=True)
    runtime_root=args.runtime_root.resolve()
    app=workspace(directory,runtime_root=runtime_root)
    if (app/'.venv').resolve()!=(runtime_root/'.venv').resolve():
        raise ValueError('Existing QA directory belongs to another runtime root; choose a new directory')
    report_path=directory/'inference.json'
    report=json.loads(report_path.read_text()) if report_path.is_file() else {'scope':'Actual smoke inference only; quality, UI, fresh install and release remain separate gates','models':{}}
    report['updatedAt']=datetime.now(timezone.utc).isoformat()
    report['runtimeRoot']=str(runtime_root)
    fingerprint=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'src/voice_cloner').glob('*.py')))+Path(models.__file__).with_name('model-catalog.json').read_bytes()).hexdigest()
    report['sourceFingerprint']=fingerprint
    fixture('kokoro',EN_REFERENCE,'qa-en','en',app,directory)
    fixture('piper-dmitri',RU_REFERENCE,'qa-ru','ru',app,directory)
    chosen=[models.model_for(i) for i in args.models] if args.models else models.CATALOG
    if any(m is None for m in chosen):raise ValueError('Unknown model ID')
    for model in chosen:
        record=report['models'].get(model['id'],{})
        if record.get('status')=='passed' and record.get('sourceFingerprint')==fingerprint and not args.repeat and (not args.resources or record.get('resources',{}).get('collector')=='macos-time-l-maxrss-v1'):continue
        record={'status':'starting','sourceFingerprint':fingerprint,'startedAt':datetime.now(timezone.utc).isoformat()}
        report['models'][model['id']]=record;atomic_json(report_path,report)
        print(model['id'],'starting',flush=True)
        try:
            if not models.ready(model,app):
                if model.get('gated'):raise RuntimeError('Author access and licensed local weights required; no bypass attempted')
                if not args.download:raise RuntimeError('Model not installed; use --download for a real installation test')
                record['status']='downloading';atomic_json(report_path,report)
                run([str(app/'.venv/bin/python'),'-u','-m','voice_cloner.models','download',model['id'],'--root',str(app)],None,'mlx-speech',app,directory/(model['id']+'-download.log'),2400,online=True)
            language='ru' if 'ru' in model['languages'] else 'en'
            before=artifact_state(model,app)
            record['status']='running';atomic_json(report_path,report)
            if model['task']=='transcription':
                job={'id':str(uuid.uuid4()),'modelId':model['id'],'type':'transcribe','sourcePath':str(app/'data/profiles'/('qa-'+language)/'reference.wav'),'language':language}
                events,seconds=run([str(runtimes.python_for(model['runtime'],app)),'-u','-m','voice_cloner.runtime_worker'],job,model['runtime'],app,directory/(model['id']+'.log'),900)
                terminal=next((e for e in reversed(events) if e.get('event')=='completed'),None)
                if not terminal or not str(terminal.get('transcript') or '').strip():raise ValueError('No transcript returned')
                record.update(seconds=seconds,transcript=terminal['transcript'],expected=RU_REFERENCE if language=='ru' else EN_REFERENCE,qualityReview='pending',events=events)
                if PROFILE_RESOURCES:record['resources']=resource_usage(directory/(model['id']+'.log'))
            else:
                record.update(generate(model,RU_TEXT if language=='ru' else EN_TEXT,app,directory,language=language,voice='qa-'+language if model.get('synthesisMode')=='clone' else None))
            after=artifact_state(model,app)
            record['modelRemainsReady']=models.ready(model,app)
            record['changedArtifacts']=[path for path in before if after.get(path)!=before[path]]
            if record['changedArtifacts'] or not record['modelRemainsReady']:
                raise ValueError('Inference changed pinned model artifacts or made the model unavailable: '+', '.join(record['changedArtifacts']))
            record['status']='passed'
        except Exception as exc:
            record.update(status='failed',error=str(exc))
        record['completedAt']=datetime.now(timezone.utc).isoformat();atomic_json(report_path,report)
        print(model['id'],record['status'],record.get('error') or record.get('seconds'),flush=True)
    return int(any(r['status']!='passed' for r in report['models'].values()))


if __name__=='__main__':raise SystemExit(main())
