#!/usr/bin/env python3
"""Install/probe optional runtimes using only the independent fresh-install dependency cache."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import runtimes
spec=importlib.util.spec_from_file_location('inference_qa',ROOT/'scripts/verify-model-inference.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)


def main():
    fresh=ROOT/'.runtime/release-audit/fresh install'
    if not (fresh/'.venv/bin/python').is_file() or (fresh/'.runtime/cache').is_symlink():
        raise ValueError('Run a genuinely independent bootstrap before this verification')
    folder=ROOT/'.runtime/release-audit/fresh-runtimes';folder.mkdir(parents=True,exist_ok=True)
    path=folder/'results.json'
    report={'scope':'Actual fresh dependency installation and offline imports, not model inference', 'runtimes':{}}
    if path.is_file():report=json.loads(path.read_text())
    program="""import subprocess,sys
from pathlib import Path
from voice_cloner import runtimes
root=Path(sys.argv[2]);name=sys.argv[1]
runtimes.install(name,root)
env=runtimes.environment(root);env.update(PYTHONPATH=runtimes.module_paths(name,root),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
subprocess.run([str(runtimes.python_for(name,root)),'-c',runtimes.SPECS[name]],cwd=root,env=env,check=True,timeout=runtimes.PROBE_TIMEOUT)
"""
    for name in runtimes.SPECS:
        previous=report['runtimes'].get(name,{})
        if previous.get('status')=='passed' and previous.get('lock')==runtimes.signature(name,fresh) and runtimes.ready(name,fresh):continue
        row={'status':'installing','startedAt':datetime.now(timezone.utc).isoformat(),'lock':runtimes.signature(name,fresh),'root':str(fresh)}
        report['runtimes'][name]=row;qa.atomic_json(path,report);print(name,'installing',flush=True)
        try:
            _,seconds=qa.run([str(fresh/'.venv/bin/python'),'-u','-c',program,name,str(fresh)],None,'mlx-speech',fresh,folder/(name+'.log'),21600)
            assert runtimes.ready(name,fresh)
            row.update(status='passed',seconds=seconds)
        except Exception as exc:row.update(status='failed',error=str(exc))
        row['completedAt']=datetime.now(timezone.utc).isoformat();qa.atomic_json(path,report);print(name,row['status'],row.get('error','')[:300],flush=True)
    return int(any(r['status']!='passed' for r in report['runtimes'].values()))


if __name__=='__main__':raise SystemExit(main())
