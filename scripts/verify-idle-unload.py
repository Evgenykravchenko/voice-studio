#!/usr/bin/env python3
"""Observe a real persistent Fish worker unloading after its configured idle period."""
import importlib.util
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import runtimes
spec=importlib.util.spec_from_file_location('inference_qa',ROOT/'scripts/verify-model-inference.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)


def rss(pid):
    value=subprocess.run(['ps','-o','rss=','-p',str(pid)],capture_output=True,text=True,check=True).stdout.strip()
    return int(value)*1024


def main():
    folder=ROOT/'.runtime/release-audit/idle';app=qa.workspace(folder)
    shutil.copytree(ROOT/'.runtime/release-audit/app/data/profiles/qa-ru',app/'data/profiles/qa-ru',dirs_exist_ok=True)
    env=runtimes.environment(app);env.update(PYTHONPATH=runtimes.module_paths('mlx-speech',app),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    report={'scope':'Persistent Fish idle unload, MLX allocation counters and observed process RSS; not total system memory', 'events':[]}
    job={'id':str(uuid.uuid4()),'modelId':'fish-s2-pro','voiceId':'qa-ru','text':'Здравствуйте. Проверяем освобождение памяти после озвучки.','language':'ru','emotion':'calm','seed':42}
    probe = """from voice_cloner import worker
import mlx.core as mx
old_generate=worker.Engine.generate
old_unload=worker.Engine.unload
def memory():
    return dict(activeBytes=mx.get_active_memory(),cacheBytes=mx.get_cache_memory(),peakBytes=mx.get_peak_memory())
def generate(self,job):
    old_generate(self,job)
    worker.emit('qa_after_generation',memory=memory())
def unload(self):
    before=memory()
    old_unload(self)
    worker.emit('qa_unloaded_memory',before=before,after=memory())
worker.Engine.generate=generate
worker.Engine.unload=unload
worker.main()
"""
    with (folder/'worker.log').open('wb') as log:
        child=subprocess.Popen([str(app/'.venv/bin/python'),'-u','-c',probe],cwd=app,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,bufsize=0)
        selector=selectors.DefaultSelector();selector.register(child.stdout,selectors.EVENT_READ);buffer=b'';start=time.monotonic();completed=None;sample=0
        try:
            while time.monotonic()-start<600:
                if time.monotonic()-sample>2:
                    sample=time.monotonic();report['peakObservedRssBytes']=max(report.get('peakObservedRssBytes',0),rss(child.pid))
                for key,_ in selector.select(timeout=.5):
                    chunk=os.read(key.fd,65536)
                    if not chunk:raise RuntimeError('Worker exited before idle unload')
                    buffer+=chunk
                    while b'\n' in buffer:
                        line,buffer=buffer.split(b'\n',1);event=json.loads(line);report['events'].append(event)
                        if event.get('event')=='ready':
                            report['baselineRssBytes']=rss(child.pid);child.stdin.write((json.dumps(job)+'\n').encode())
                        elif event.get('event')=='failed':raise RuntimeError(event.get('error'))
                        elif event.get('event')=='completed':
                            completed=time.monotonic();report['afterGenerationRssBytes']=rss(child.pid);report['audio']=qa.audio_metrics(app/'outputs/studio'/(job['id']+'.wav'));print('generated; observing configured180s idle period',flush=True)
                        elif event.get('event')=='qa_after_generation':report['afterGenerationMlx']=event['memory']
                        elif event.get('event')=='unloaded' and completed:
                            report['idleSeconds']=round(time.monotonic()-completed,2);report['afterUnloadRssBytes']=rss(child.pid)
                            assert 179<=report['idleSeconds']<190,report['idleSeconds']
                            assert child.poll() is None
                        elif event.get('event')=='qa_unloaded_memory' and completed:
                            report['unloadedMlx']=dict(before=event['before'],after=event['after'])
                            assert event['before']['activeBytes']>1_000_000_000
                            assert event['after']['activeBytes']<1_000_000
                            assert event['after']['cacheBytes']==0
                            report['status']='passed';qa.atomic_json(folder/'result.json',report);print({k:v for k,v in report.items() if k!='events'},flush=True);return 0
            raise TimeoutError('No idle unload event within observed limit')
        finally:
            selector.close();child.terminate()
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait()
    return 1


if __name__=='__main__':raise SystemExit(main())
