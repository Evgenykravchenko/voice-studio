#!/usr/bin/env python3
"""Inspect Mach-O load commands for undeclared external libraries; dlopen remains a runtime gate."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import runtimes
MAGIC={b'\xcf\xfa\xed\xfe',b'\xce\xfa\xed\xfe',b'\xca\xfe\xba\xbe',b'\xca\xfe\xba\xbf'}


def inspect(path):
    with path.open('rb') as stream:
        if stream.read(4) not in MAGIC:return None
    commands=subprocess.run(['/usr/bin/otool','-l',str(path)],check=True,capture_output=True,text=True).stdout
    deps=[];rpaths=[];identifiers=[];minimum=[];command=None;platform_name=None
    loads={'LC_LOAD_DYLIB','LC_LOAD_WEAK_DYLIB','LC_REEXPORT_DYLIB','LC_LOAD_UPWARD_DYLIB','LC_LAZY_LOAD_DYLIB'}
    for raw in commands.splitlines():
        line=raw.strip()
        if line.startswith('cmd '):command=line[4:];platform_name=None
        elif command in loads and line.startswith('name '):deps.append(line[5:].split(' (offset')[0])
        elif command=='LC_ID_DYLIB' and line.startswith('name '):identifiers.append(line[5:].split(' (offset')[0])
        elif command=='LC_RPATH' and line.startswith('path '):rpaths.append(line[5:].split(' (offset')[0])
        elif command=='LC_BUILD_VERSION' and line.startswith('platform '):platform_name=line[9:]
        elif command=='LC_BUILD_VERSION' and platform_name=='MACOS' and line.startswith('minos '):minimum.append(line[6:])
        elif command=='LC_VERSION_MIN_MACOSX' and line.startswith('version '):minimum.append(line[8:])
    return {'file':str(path),'dependencies':deps,'rpaths':rpaths,'installNames':identifiers,'minimumMacOS':minimum}



def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--output',type=Path,default=ROOT/'.runtime/release-audit/native-links.json');args=parser.parse_args();root=args.root.resolve()
    names=['mlx-speech',*[name for name in runtimes.SPECS if runtimes.ready(name,root)]]
    files=set();interpreters={};violations=[]
    for name in names:
        binary=runtimes.python_for(name,root);interpreters[name]=str(binary.resolve())
        if not binary.resolve().is_relative_to(root):violations.append({'runtime':name,'interpreter':str(binary.resolve())})
        if binary.is_file():files.add(binary.resolve())
        folder=binary.parent.parent
        for path in folder.rglob('*'):
            if path.is_file() and path.suffix in {'.so','.dylib'}:files.add(path.resolve())
    records=[v for v in ThreadPoolExecutor(max_workers=4).map(inspect,sorted(files)) if v]
    def external(value):
        return value.startswith('/') and value not in ('/usr/lib','/System/Library') and not value.startswith(('/usr/lib/','/System/Library/')) and not Path(value).is_relative_to(root)
    dependencies=[{'file':r['file'],'dependency':d} for r in records for d in r['dependencies'] if external(d)]
    search=[{'file':r['file'],'rpath':p} for r in records for p in r['rpaths'] if external(p)]
    minimum=[{'file':r['file'],'minimum':version} for r in records for version in r['minimumMacOS'] if tuple((list(map(int,version.split('.')))+[0,0])[:3])>(14,0,0)]
    result={'scope':'Static Mach-O commands and interpreter isolation only; relative rpath resolution, dlopen and actual inference are separate checks',
            'root':str(root),'runtimes':names,'interpreters':interpreters,'interpreterViolations':violations,
            'externalDependencies':dependencies,'externalSearchPaths':search,'newerThanMacOS14':minimum,'objects':records}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'runtimes':len(names),'nativeObjects':len(records),'externalDependencies':len(dependencies),'externalSearchPaths':len(search),'interpreterViolations':len(violations),'newerThanMacOS14':len(minimum),'report':str(args.output)}))
    return int(bool(dependencies or violations or minimum))


if __name__=='__main__':raise SystemExit(main())
