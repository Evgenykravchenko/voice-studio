#!/usr/bin/env python3
"""Maintainer-only native wheels; end users install the checked-in binaries without Xcode."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import runtimes


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    if platform.system()!='Darwin' or platform.machine()!='arm64' or sys.version_info[:2]!=(3,13):
        raise RuntimeError('Build on macOS ARM64 with the project Python3.13')
    folder=ROOT/'engines/wheels';sources=json.loads((folder/'source-manifest.json').read_text())
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--packages',nargs='*',choices=sorted(sources));args=parser.parse_args()
    env=runtimes.environment(ROOT)
    env.update(MACOSX_DEPLOYMENT_TARGET='14.0',ARCHFLAGS='-arch arm64',CFLAGS='-O2 -arch arm64 -mmacosx-version-min=14.0',
               CXXFLAGS='-O2 -arch arm64 -mmacosx-version-min=14.0',CMAKE_OSX_DEPLOYMENT_TARGET='14.0',
               CMAKE_BUILD_PARALLEL_LEVEL='4',SOURCE_DATE_EPOCH='1704067200')
    stage=ROOT/'.runtime/native-wheel-build';stage.mkdir(parents=True,exist_ok=True)
    report={'platform':'macOS ARM64','deploymentTarget':'14.0','sourceDateEpoch':env['SOURCE_DATE_EPOCH'],
            'buildConstraintsSha256':digest(ROOT/'engines/wheel-build.lock'),'wheels':[]}
    if (folder/'manifest.json').is_file():report['wheels']=json.loads((folder/'manifest.json').read_text())['wheels']
    for name in args.packages or sources:
        source=sources[name];archive=folder/'sources'/source['name']
        if digest(archive)!=source['sha256']:raise RuntimeError('Source archive checksum mismatch: '+name)
        python_version=source.get('python','3.13');abi='cp'+python_version.replace('.','');build_source=archive
        binary=ROOT/'.venv/bin/python' if python_version=='3.13' else runtimes.python_for('cosyvoice',ROOT)
        version=source.get('wheelVersion',source['version'])
        if source.get('patch'):
            patch=folder/source['patch']
            if digest(patch)!=source['patchSha256']:raise RuntimeError('Source patch checksum mismatch: '+name)
            unpack=stage/(name+'-source');unpack.mkdir(exist_ok=True)
            with tarfile.open(archive) as stream:stream.extractall(unpack,filter='data')
            build_source=unpack/(name+'-'+source['version'])
            subprocess.run(['/usr/bin/patch','-p1','--input',str(patch)],cwd=build_source,check=True)
        subprocess.run([str(ROOT/'.runtime/bin/uv'),'build','--wheel','--python',str(binary),
                        '--build-constraints',str(ROOT/'engines/wheel-build.lock'),'--out-dir',str(stage),str(build_source)],
                       env=env,cwd=ROOT,check=True,timeout=1800)
        wheels=list(stage.glob(name+'-'+version+'-'+abi+'-'+abi+'-macosx_14_0_arm64.whl'))
        if len(wheels)!=1:raise RuntimeError('Unexpected wheel ABI/platform: '+name)
        wheel=wheels[0]
        with zipfile.ZipFile(wheel) as package:
            if package.testzip() is not None:raise RuntimeError('Corrupt wheel')
            if any(b'/Users/' in package.read(path) for path in package.namelist() if path.endswith('.so')):raise RuntimeError('Personal build path leaked into wheel')
        target=folder/wheel.name;target.write_bytes(wheel.read_bytes())
        report['wheels']=[item for item in report['wheels'] if item['name']!=name]
        report['wheels'].append({'name':name,'version':version,'upstreamVersion':source['version'],'python':python_version,'file':target.name,'sha256':digest(target),
                                'sourceSha256':source['sha256'],'patchSha256':source.get('patchSha256'),'size':target.stat().st_size})
    report['pythonVersions']=sorted({item.get('python','3.13') for item in report['wheels']})
    (folder/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
