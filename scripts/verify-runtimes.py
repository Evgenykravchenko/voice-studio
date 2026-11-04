#!/usr/bin/env python3
"""Re-run isolated offline import probes; these are not inference smoke tests."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import runtimes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.runtime/release-audit/runtimes.json')
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--dynamic-libraries',action='store_true',help='Inspect libraries actually loaded by each offline import on macOS')
    args=parser.parse_args()
    root=args.root.resolve()
    results=[]
    specs={'mlx-speech':'import mlx_speech, mlx.core, soundfile', 'mlx-whisper':'import mlx_whisper, mlx.core', **runtimes.SPECS}
    for name,probe in specs.items():
        start=time.monotonic()
        folder=ROOT/'.runtime/release-audit/runtime-logs';folder.mkdir(parents=True,exist_ok=True)
        env=runtimes.environment(root)
        env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONPATH=runtimes.module_paths(name,root))
        binary=runtimes.python_for(name,root)
        entry={'runtime':name,'readinessMarker':runtimes.ready(name,root),'probe':probe,'status':'missing'}
        code=probe
        if args.dynamic_libraries:
            code+='''
import ctypes,json,sys
image=ctypes.CDLL(None)
image._dyld_image_count.restype=ctypes.c_uint32
image._dyld_get_image_name.argtypes=[ctypes.c_uint32]
image._dyld_get_image_name.restype=ctypes.c_char_p
names=[image._dyld_get_image_name(i).decode() for i in range(image._dyld_image_count())]
print(json.dumps({'voiceStudioNativeLibraries':names,'interpreter':sys.executable}))
'''
        if binary.is_file():
            with (folder/(name+'.log')).open('w') as log:
                process=subprocess.Popen([str(binary),'-c',code],env=env,cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                try:
                    code=process.wait(timeout=runtimes.PROBE_TIMEOUT)
                    entry.update(status='passed' if code==0 else 'failed',exitCode=code)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.wait()
                    entry.update(status='timeout')
            if args.dynamic_libraries and entry['status']=='passed':
                records=[]
                for line in (folder/(name+'.log')).read_text().splitlines():
                    try:value=json.loads(line)
                    except ValueError:continue
                    if isinstance(value,dict) and 'voiceStudioNativeLibraries' in value:records.append(value)
                if not records:entry.update(status='failed',error='Missing native-library inspection')
                else:
                    libraries=records[-1]['voiceStudioNativeLibraries']
                    outside=[path for path in libraries if not path.startswith(('/usr/lib/','/System/Library/','/System/Volumes/Preboot/Cryptexes/OS/')) and not Path(path).resolve().is_relative_to(root)]
                    entry.update(nativeLibraries=libraries,externalNativeLibraries=outside)
                    if outside:entry.update(status='failed',error='Native libraries outside the project/system')
        entry['seconds']=round(time.monotonic()-start,2)
        results.append(entry)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps({'generatedAt':datetime.now(timezone.utc).isoformat(),'scope':'Offline imports only; not a proof of model inference','runtimes':results},indent=2)+'\n')
        print(json.dumps({k:v for k,v in entry.items() if k not in ['nativeLibraries','externalNativeLibraries']} | {'externalNativeLibraries':len(entry.get('externalNativeLibraries',[]))}),flush=True)
    return int(any(r['status']!='passed' for r in results))


if __name__=='__main__':raise SystemExit(main())
