"""Release artifacts must match the portable runtime lock, not a developer's wheel cache."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]


class NativeWheelArtifactsTests(unittest.TestCase):
    def test_source_and_binary_hashes_metadata_and_portable_lock_agree(self):
        folder=ROOT/'engines/wheels';manifest=json.loads((folder/'manifest.json').read_text());sources=json.loads((folder/'source-manifest.json').read_text())
        self.assertEqual({'mojimoji','pyopenjtalk','webrtcvad'},{item['name'] for item in manifest['wheels']})
        for item in manifest['wheels']:
            with self.subTest(package=item['name']):
                lock=(ROOT/'engines'/('cosyvoice.lock' if item['name']=='webrtcvad' else 'mlx-audio-extended.lock')).read_text()
                self.assertNotIn('/Users/',lock)
                abi='cp311' if item['name']=='webrtcvad' else 'cp313'
                self.assertTrue(item['file'].endswith('-'+abi+'-'+abi+'-macosx_14_0_arm64.whl'))
                artifact=folder/item['file']
                self.assertEqual(item['sha256'],hashlib.sha256(artifact.read_bytes()).hexdigest())
                source=sources[item['name']]
                self.assertEqual(item['sourceSha256'],hashlib.sha256((folder/'sources'/source['name']).read_bytes()).hexdigest())
                self.assertEqual(source['sha256'],item['sourceSha256'])
                if source.get('patch'):
                    self.assertEqual(item['patchSha256'],hashlib.sha256((folder/source['patch']).read_bytes()).hexdigest())
                self.assertIn(item['name']+' @ file:engines/wheels/'+item['file'],lock)
                self.assertIn('--hash=sha256:'+item['sha256'],lock)
                with zipfile.ZipFile(artifact) as archive:
                    self.assertIsNone(archive.testzip())
                    metadata=next(name for name in archive.namelist() if name.endswith('.dist-info/METADATA'))
                    text=archive.read(metadata).decode()
                    self.assertIn('Name: '+item['name'],text)
                    self.assertIn('Version: '+item['version'],text)
                    self.assertTrue(any('license' in name.lower() for name in archive.namelist()))
                    for name in archive.namelist():
                        if name.endswith('.so'):self.assertNotIn(b'/Users/',archive.read(name))


if __name__=='__main__':unittest.main()
