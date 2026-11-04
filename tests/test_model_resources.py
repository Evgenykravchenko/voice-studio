import hashlib
from contextlib import chdir
from pathlib import Path
import shlex
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

from voice_cloner import model_resources, models


class DictionaryBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dictionary project ')
        self.root = Path(self.temp.name)
        self.archive = self.root / 'dictionary.zip'

    def tearDown(self):
        self.temp.cleanup()

    def entry(self, extra=None):
        with zipfile.ZipFile(self.archive, 'w') as archive:
            for name in model_resources.DICTIONARY_FILES[:-1]:
                archive.writestr('unidic/' + name, b'dictionary data')
            archive.writestr('unidic/COPYING', 'Dictionary license')
            if extra:
                archive.writestr(*extra)
        entry = {'id': 'test', 'repo': 'author/model', 'revision': 'a' * 40,
                 'files': [{'path': 'dictionary.zip', 'url': 'https://example.invalid/dictionary.zip',
                            'size': self.archive.stat().st_size, 'resource': 'unidic',
                            'sha256': hashlib.sha256(self.archive.read_bytes()).hexdigest()}]}
        target = models.file_path(entry, entry['files'][0], self.root)
        target.parent.mkdir(parents=True)
        target.write_bytes(self.archive.read_bytes())
        return entry

    def test_dictionary_prepared_locally_with_license_and_repaired_if_incomplete(self):
        entry = self.entry()
        self.assertFalse(model_resources.ready(entry, self.root))
        model_resources.prepare(entry, self.root)
        dictionary = model_resources.dictionary(entry, self.root)
        self.assertIsNotNone(dictionary)
        self.assertEqual('Dictionary license', (dictionary / 'COPYING').read_text())
        (dictionary / 'matrix.bin').unlink()
        self.assertFalse(model_resources.ready(entry, self.root))
        model_resources.prepare(entry, self.root)
        self.assertTrue(model_resources.ready(entry, self.root))
        marker = model_resources.location(entry, self.root) / 'prepared.json'
        marker.write_text('{"files": []}')
        self.assertFalse(model_resources.ready(entry, self.root))

    def test_invalid_or_unsafe_bundle_never_becomes_ready(self):
        entry = self.entry(('../outside.txt', 'escape'))
        with self.assertRaisesRegex(ValueError, 'путь'):
            model_resources.prepare(entry, self.root)
        self.assertFalse((self.root / 'outside.txt').exists())
        self.assertFalse(model_resources.ready(entry, self.root))
        self.assertEqual([], list(model_resources.location(entry, self.root).parent.glob('.dictionary-*')))
        target = models.file_path(entry, entry['files'][0], self.root)
        target.write_bytes(b'corrupted')
        with self.assertRaisesRegex(ValueError, 'повреждён'):
            model_resources.prepare(entry, self.root)

    def test_missing_dictionary_blocks_model_selection_even_when_archive_is_present(self):
        entry = self.entry()
        entry.update(task='synthesis', integration='ready', runtime='mlx-speech', sizeBytes=entry['files'][0]['size'])
        binary=self.root/'.venv/bin/python';binary.parent.mkdir(parents=True);binary.touch()
        (binary.parent.parent/'pyvenv.cfg').write_text('home = '+str(binary.parent)+'\n')
        self.assertTrue(models.installed(entry, self.root))
        self.assertFalse(models.ready(entry, self.root))
        model_resources.prepare(entry, self.root)
        self.assertTrue(models.ready(entry, self.root))

    def test_pipeline_uses_explicit_paths_with_spaces_and_restores_tagger(self):
        entry = self.entry()
        model_resources.prepare(entry, self.root)
        directory = model_resources.dictionary(entry, self.root)
        tagger = object()
        misaki = types.ModuleType('misaki')
        misaki.cutlet = types.SimpleNamespace(Tagger=tagger)
        calls = []
        fugashi = types.ModuleType('fugashi')
        fugashi.Tagger = lambda options: calls.append(shlex.split(options))
        class Voice:
            def _get_pipeline(self, code):
                self.code = code
                misaki.cutlet.Tagger()
                raise RuntimeError('pipeline failed')
        with patch.dict(sys.modules, {'misaki': misaki, 'fugashi': fugashi}), patch.object(model_resources, 'dictionary', return_value=directory):
            with self.assertRaisesRegex(RuntimeError, 'pipeline failed'):
                model_resources.initialize_japanese(Voice(), entry)
        self.assertIs(tagger, misaki.cutlet.Tagger)
        self.assertEqual([['-r', str(directory / 'mecabrc'), '-d', str(directory)]], calls)

    def test_espeak_native_path_is_shortened_only_during_pipeline_creation(self):
        base = self.root / ('deep project with spaces ' * 6)
        work = base / '.runtime/work/extended'
        data = base / '.runtime/engines/extended/data'
        work.mkdir(parents=True)
        data.mkdir(parents=True)
        calls = []
        class API:
            def __init__(self, library, data_path):
                calls.append((library, data_path))
        original = API.__init__
        api = types.ModuleType('phonemizer.backend.espeak.api')
        api.EspeakAPI = API
        class Voice:
            def _get_pipeline(self, code):
                self.code = code
                API('local library', data)
                raise RuntimeError('pipeline failed')
        with patch.dict(sys.modules, {'phonemizer.backend.espeak.api': api}), chdir(work):
            with self.assertRaisesRegex(RuntimeError, 'pipeline failed'):
                model_resources.initialize_kokoro(Voice(), {}, 'af_heart')
            self.assertIs(original, API.__init__)
            self.assertEqual(data.resolve(), Path(calls[0][1]).resolve())
            self.assertFalse(Path(calls[0][1]).is_absolute())
            self.assertLess(len(calls[0][1]), 100)


if __name__ == '__main__':
    unittest.main()
