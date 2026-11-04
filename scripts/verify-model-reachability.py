#!/usr/bin/env python3
"""Probe anonymous first-byte access to each pinned model repository/component.

This is not a complete transfer, resume, checksum or inference test. No credentials,
access-gate workarounds, insecure TLS or model mirrors are used. Model bodies are closed
after one byte even when the server ignores Range. Gated catalog entries remain untested.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import models


def probe(item):
    repo,revision,path,url,size,users=item
    evidence=dict(repo=repo,revision=revision,path=path,url=url,models=users)
    try:
        request=Request(url,headers={'Range':'bytes=0-0','Accept-Encoding':'identity','User-Agent':'voice-studio-readiness-probe'})
        with urlopen(request,timeout=20) as response:
            first=response.read(1)
            if not first:raise ValueError('Empty response body')
            ranged=response.headers.get('Content-Range')
            if response.status==206 and size and ranged!=f'bytes 0-0/{size}':
                raise ValueError('Unexpected range or artifact size')
            if response.status not in [200,206]:raise ValueError('Unexpected HTTP status')
            evidence.update(status='reachable',httpStatus=response.status,contentRange=ranged,bytesRead=1)
    except HTTPError as exc:evidence.update(status='unverified',httpStatus=exc.code,error='HTTP '+str(exc.code))
    except (OSError,ValueError) as exc:evidence.update(status='unverified',error=type(exc).__name__+': '+str(exc))
    return evidence


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models',nargs='+')
    parser.add_argument('--output',type=Path,default=ROOT/'.runtime/release-audit/model-reachability.json')
    args=parser.parse_args();chosen=[models.model_for(id) for id in args.models] if args.models else models.CATALOG
    if any(model is None for model in chosen):raise ValueError('Unknown model')
    groups={};excluded=[]
    for model in chosen:
        if model.get('gated'):
            excluded.append({'id':model['id'],'reason':'Licensed author access required; no weight request attempted'});continue
        for file in model['files']:
            repo=file.get('repo',model['repo']);revision=file.get('revision',model['revision'])
            key=(repo,revision,file.get('url'))
            size=file.get('size') or 0
            if key not in groups:groups[key]={'file':file,'size':size,'models':set()}
            groups[key]['models'].add(model['id'])
            if size>groups[key]['size']:groups[key].update(file=file,size=size)
    jobs=[]
    for (repo,revision,direct),group in groups.items():
        file=group['file'];path=file['path']
        url=direct or f"https://huggingface.co/{quote(repo,safe='/')}/resolve/{quote(revision,safe='')}/{quote(path,safe='/')}"
        jobs.append((repo,revision,path,url,group['size'],sorted(group['models'])))
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(probe,jobs))
    report={'scope':__doc__,'generatedAt':datetime.now(timezone.utc).isoformat(),'excludedGated':excluded,'probes':results}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'probes':len(results),'reachable':sum(x['status']=='reachable' for x in results),'unverified':[x for x in results if x['status']!='reachable'],'excludedGated':excluded},ensure_ascii=False),flush=True)
    return int(any(x['status']!='reachable' for x in results))


if __name__=='__main__':raise SystemExit(main())
