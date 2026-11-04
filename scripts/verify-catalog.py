#!/usr/bin/env python3
"""Read-only catalog evidence: local presence and pinned author manifests, never inference proof."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from voice_cloner import models


def remote_manifest(key):
    repo, revision = key
    url = 'https://huggingface.co/api/models/' + quote(repo, safe='/') + '/revision/' + quote(revision, safe='') + '?blobs=true'
    try:
        with urlopen(Request(url, headers={'User-Agent': 'voice-studio-catalog-verifier'}), timeout=40) as response:
            value = json.load(response)
        return key, {'sha': value['sha'], 'gated': value.get('gated', False), 'files': {f['rfilename']: f for f in value['siblings']}}
    except (OSError, ValueError, KeyError) as exc:
        return key, {'error': str(exc), 'httpStatus': exc.code if isinstance(exc, HTTPError) else None}


def audit(*, remote=False, hash_local=False):
    entries = models.inventory(ROOT)['models']
    manifests = {}
    if remote:
        keys = {(f.get('repo', m['repo']), f.get('revision', m['revision'])) for m in models.CATALOG for f in m['files'] if not f.get('url')}
        with ThreadPoolExecutor(max_workers=4) as pool:
            manifests = dict(pool.map(remote_manifest, sorted(keys)))
    result = []
    for model, local in zip(models.CATALOG, entries):
        issues, remote_files, hashes = [], [], []
        if sum(f['size'] for f in model['files']) != model['sizeBytes'] and not model.get('dynamicArtifact'):
            issues.append('Catalog total differs from required files')
        for f in model['files']:
            p = PurePosixPath(f['path'])
            if p.is_absolute() or '..' in p.parts:
                issues.append('Unsafe file path: ' + f['path'])
            if not f.get('url') and not re.fullmatch('[a-f0-9]{40}', f.get('revision', model['revision'])):
                issues.append('Unpinned revision: ' + f['path'])
            if remote and not f.get('url'):
                info = manifests[(f.get('repo', model['repo']), f.get('revision', model['revision']))]
                evidence = {'path': f['path'], 'repo': f.get('repo', model['repo'])}
                if 'error' in info:
                    evidence.update(status='unverified', error=info['error'], httpStatus=info['httpStatus'])
                else:
                    author_file = info['files'].get(f['path'])
                    evidence.update(revision=info['sha'], gated=info['gated'])
                    if author_file is None:
                        evidence.update(status='missing')
                    elif author_file.get('size') != f['size']:
                        evidence.update(status='size-mismatch', expected=f['size'], actual=author_file.get('size'))
                    elif f.get('sha256') and author_file.get('lfs', {}).get('sha256') != f['sha256']:
                        evidence.update(status='hash-mismatch', expected=f['sha256'], actual=author_file.get('lfs', {}).get('sha256'))
                    else:
                        evidence.update(status='verified')
                remote_files.append(evidence)
            elif remote:
                try:
                    with urlopen(Request(f['url'], method='HEAD'), timeout=40) as response:
                        remote_files.append({'path': f['path'], 'status': 'url-reachable', 'httpStatus': response.status, 'length': response.headers.get('Content-Length')})
                except OSError as exc:
                    remote_files.append({'path': f['path'], 'status': 'unverified', 'error': str(exc)})
            if hash_local and local['installed']:
                target = models.file_path(model, f, ROOT)
                expected = f.get('sha256')
                if expected:
                    with target.open('rb') as stream:
                        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                    hashes.append({'path': f['path'], 'status': 'verified' if digest == expected else 'hash-mismatch'})
        result.append({'id': model['id'], 'name': model['name'], 'task': model['task'], 'adapter': model['adapter'], 'runtime': model['runtime'], 'gated': model.get('gated', False), 'sizeBytes': local['sizeBytes'], 'installed': local['installed'], 'runtimeReady': local['runtimeReady'], 'structureIssues': issues, 'remoteFiles': remote_files, 'localHashes': hashes, 'inference': 'unverified'})
    return {'generatedAt': datetime.now(timezone.utc).isoformat(), 'catalogSha256': hashlib.sha256(Path(models.__file__).with_name('model-catalog.json').read_bytes()).hexdigest(), 'scope': 'Catalog structure, local files, optional author manifests/hashes. Does not establish inference or production readiness.', 'remoteRequested': remote, 'localHashesRequested': hash_local, 'models': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--hash-local', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / '.runtime/release-audit/catalog.json')
    args = parser.parse_args()
    report = audit(remote=args.remote, hash_local=args.hash_local)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    entries = report['models']
    failures = [(m['id'], f) for m in entries for f in m['remoteFiles'] + m['localHashes'] if f['status'] not in ('verified', 'url-reachable')]
    print(json.dumps({'models': len(entries), 'installed': sum(m['installed'] for m in entries), 'structureIssues': sum(len(m['structureIssues']) for m in entries), 'artifactFailures': len(failures), 'report': str(args.output)}, ensure_ascii=False))
    for model_id, evidence in failures:
        print(model_id, json.dumps(evidence, ensure_ascii=False))
    return int(bool(failures or any(m['structureIssues'] for m in entries)))


if __name__ == '__main__':
    raise SystemExit(main())
