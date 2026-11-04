#!/usr/bin/env python3
"""Keep release metadata consistent; allow only vX.Y.Z and vX.Y.Z-snapshot tags."""
import argparse
import json
from pathlib import Path
import re
import tomllib
from xml.etree import ElementTree


def check(root, tag=None):
    version = tomllib.loads((root / 'pyproject.toml').read_text())['project']['version']
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('Application version must be X.Y.Z')
    versions = {
        'frontend': json.loads((root / 'frontend/package.json').read_text())['version'],
        'Java API': ElementTree.parse(root / 'server/pom.xml').findtext('{http://maven.apache.org/POM/4.0.0}version'),
        'Python lock': next(p['version'] for p in tomllib.loads((root / 'uv.lock').read_text())['package'] if p['name'] == 'fish-voice-cloner'),
    }
    if any(value != version for value in versions.values()):
        raise ValueError(f'Version mismatch: Python={version}, {versions}')
    if tag is not None and tag not in ('v' + version, 'v' + version + '-snapshot'):
        raise ValueError('Tag must match the application version: vX.Y.Z or vX.Y.Z-snapshot')
    return version


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag')
    args = parser.parse_args()
    print('Release metadata passed: ' + check(Path(__file__).resolve().parents[1], args.tag))
