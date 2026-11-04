#!/usr/bin/env python3
"""Exercise real catalog installers serially, without changing active selections or user data.

May download over100GB. Uses only project-local model/runtime caches. By default existing
verified files are reused. --artifact-root exercises a separate weights-only cache;
its initial emptiness and runtime installation must be recorded independently.
"""
import argparse
import hashlib
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import models,runtimes


def save(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models',nargs='*')
    parser.add_argument('--directory',type=Path,default=ROOT/'.runtime/release-audit',help='Separate report/log directory for a disjoint installer batch')
    parser.add_argument('--artifact-root',type=Path,help='Independent weights-only test cache under this project .runtime; runtime installation is verified separately')
    parser.add_argument('--max-seconds',type=int,default=86400,help='Absolute per-model limit; progress is allowed on slow connections')
    parser.add_argument('--idle-seconds',type=int,default=600,help='Stop an installer only after this long without progress')
    args=parser.parse_args();folder=args.directory.resolve();folder.mkdir(parents=True,exist_ok=True)
    target=ROOT
    if args.artifact_root:
        target=args.artifact_root.resolve()
        if not target.is_relative_to(ROOT/'.runtime') or target==ROOT/'.runtime':
            raise ValueError('Independent download cache must be inside this project .runtime')
        target.mkdir(parents=True,exist_ok=True)
        for relative in ['.runtime/cache','.runtime/cache/huggingface/hub','.runtime/cache/artifacts']:
            if not (target/relative).resolve().is_relative_to(target):
                raise ValueError('Independent artifact cache must not link to the working installation')
    scope='Actual weights-only catalog installation into an independent cache; dependency/runtime and inference gates remain separate' if args.artifact_root else 'Actual catalog installation with shared project-local cache; not clean-install or inference proof'
    path=folder/'downloads.json';report=json.loads(path.read_text()) if path.is_file() else {'scope':scope,'artifactRoot':str(target),'catalogSha256':hashlib.sha256(Path(models.__file__).with_name('model-catalog.json').read_bytes()).hexdigest(),'installerSha256':hashlib.sha256(Path(models.__file__).read_bytes()).hexdigest(),'models':{}}
    if report.get('artifactRoot',str(ROOT))!=str(target):raise ValueError('Existing report belongs to another artifact root')
    chosen=[models.model_for(i) for i in args.models] if args.models else models.CATALOG
    if any(m is None for m in chosen):raise ValueError('Unknown model')
    if not args.models:chosen=sorted(chosen,key=lambda m:m['sizeBytes'] or 0)
    for model in chosen:
        present=models.installed(model,target) if args.artifact_root else models.ready(model,ROOT)
        if present:
            report['models'].setdefault(model['id'],{'status':'cached','note':'Already installed in the selected cache; presence/hash check is tracked separately'})
            save(path,report);continue
        record={'status':'starting','startedAt':datetime.now(timezone.utc).isoformat()};report['models'][model['id']]=record;save(path,report)
        if model.get('gated'):
            record.update(status='requires-author-access',error='User must obtain licensed author weights; not bypassed');save(path,report);continue
        print(model['id'],'starting',flush=True)
        env=runtimes.environment(target);env.update(PYTHONPATH=str(ROOT/'src'),HF_HUB_OFFLINE='0',TRANSFORMERS_OFFLINE='0',HF_HUB_DISABLE_XET='1')
        start=time.monotonic();last_activity=start;last_sizes=None
        with (folder/(model['id']+'-install.log')).open('w') as err,(folder/(model['id']+'-install.jsonl')).open('w') as out:
            program='from pathlib import Path; import sys; from voice_cloner.models import download; download(sys.argv[1],Path(sys.argv[2]),prepare=sys.argv[3]=="1")'
            child=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-u','-c',program,model['id'],str(target),'0' if args.artifact_root else '1'],cwd=ROOT,env=env,stdout=out,stderr=err,start_new_session=True)
            try:
                while True:
                    try:
                        code=child.wait(timeout=10);break
                    except subprocess.TimeoutExpired:
                        sizes=tuple((folder/(model['id']+suffix)).stat().st_size for suffix in ['-install.jsonl','-install.log'])
                        now=time.monotonic()
                        if sizes!=last_sizes:last_activity=now;last_sizes=sizes
                        if now-start>args.max_seconds or now-last_activity>args.idle_seconds:
                            raise
                
                complete=models.installed(model,target) if args.artifact_root else models.ready(model,ROOT)
                record.update(status='passed' if code==0 and complete else 'failed',exitCode=code)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGKILL);child.wait();record.update(status='timeout')
            except KeyboardInterrupt:
                os.killpg(child.pid,signal.SIGKILL);child.wait();record.update(status='cancelled');save(path,report);raise
            record.update(seconds=round(time.monotonic()-start,2),completedAt=datetime.now(timezone.utc).isoformat());save(path,report)
        print(model['id'],record['status'],record['seconds'],flush=True)
    return int(any(r['status'] not in ['passed','cached'] for r in report['models'].values()))


if __name__=='__main__':raise SystemExit(main())
