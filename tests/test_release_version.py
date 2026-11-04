import json
from pathlib import Path
import runpy
import tempfile
import unittest

check = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/check-version.py'))['check']


class ReleaseVersionTests(unittest.TestCase):
    def test_release_and_snapshot_are_the_only_tags_for_matching_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'frontend').mkdir(); (root / 'server').mkdir()
            (root / 'pyproject.toml').write_text('[project]\nversion="0.1.0"\n')
            (root / 'uv.lock').write_text('[[package]]\nname="fish-voice-cloner"\nversion="0.1.0"\n')
            (root / 'frontend/package.json').write_text(json.dumps({'version': '0.1.0'}))
            (root / 'server/pom.xml').write_text('<project xmlns="http://maven.apache.org/POM/4.0.0"><version>0.1.0</version></project>')
            for tag in (None, 'v0.1.0', 'v0.1.0-snapshot'):
                self.assertEqual(check(root, tag), '0.1.0')
            for tag in ('0.1.0', 'v0.1', 'v0.1.0-beta.1', 'v0.1.0-rc.1', 'v0.1.0-SNAPSHOT', 'v0.1.1'):
                with self.subTest(tag=tag), self.assertRaises(ValueError): check(root, tag)
            (root / 'frontend/package.json').write_text(json.dumps({'version': '0.0.0'}))
            with self.assertRaisesRegex(ValueError, 'mismatch'): check(root, 'v0.1.0')
