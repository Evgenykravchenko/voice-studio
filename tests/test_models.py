import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from voice_cloner import models


class ModelCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.entry = {'id': 'test-model', 'name': 'Test model', 'repo': 'test/model', 'revision': 'abc123',
                      'task': 'transcription', 'sizeBytes': 7,
                      'files': [{'path': 'config.json', 'size': 2}, {'path': 'weights.npz', 'size': 5}]}
        self.catalog = patch.object(models, 'CATALOG', [self.entry]); self.catalog.start()
        self.defaults = patch.object(models, 'DEFAULTS', {'transcription': 'test-model'}); self.defaults.start()

    def tearDown(self):
        self.defaults.stop(); self.catalog.stop(); self.temporary.cleanup()

    def files(self):
        folder = models.snapshot(self.entry, self.root); folder.mkdir(parents=True)
        (folder / 'config.json').write_bytes(b'{}')
        (folder / 'weights.npz').write_bytes(b'12345')
        return folder

    def test_empty_and_partial_cache_never_claim_installation(self):
        self.assertFalse(models.installed(self.entry, self.root))
        folder = self.files()
        (folder / 'weights.npz').write_bytes(b'1234')
        self.assertEqual(2, models.installed_bytes(self.entry, self.root))
        self.assertFalse(models.inventory(self.root)['models'][0]['active'])
        with self.assertRaisesRegex(ValueError, 'скачайте'):
            models.selected_path('transcription', self.root)
        with self.assertRaises(ValueError): models.select('test-model', self.root)

    def test_fully_transferred_but_unverified_download_is_not_ready(self):
        self.files()
        marker = models.validation_marker(self.entry, self.root)
        marker.parent.mkdir(parents=True); marker.touch()
        self.assertFalse(models.installed(self.entry, self.root))
        self.assertFalse(models.inventory(self.root)['models'][0]['active'])
        with self.assertRaises(ValueError): models.select('test-model', self.root)
        marker.unlink()
        self.assertTrue(models.installed(self.entry, self.root))

    def test_selection_is_durable_and_local_only(self):
        folder = self.files()
        models.select('test-model', self.root)
        self.assertEqual('test-model', models.selections(self.root)['transcription'])
        self.assertEqual(str(folder), models.selected_path('transcription', self.root))
        self.assertTrue(models.inventory(self.root)['models'][0]['active'])
        with self.assertRaises(ValueError): models.select('../../outside', self.root)

    def test_downloaded_unconnected_weights_cannot_be_selected(self):
        self.files(); self.entry['integration'] = 'files'
        self.assertTrue(models.installed(self.entry, self.root))
        self.assertFalse(models.inventory(self.root)['models'][0]['active'])
        with self.assertRaisesRegex(ValueError, 'движок'): models.select('test-model', self.root)

    def test_external_and_gated_models_never_fake_installation_or_download(self):
        self.entry.update(files=[], sizeBytes=None, integration='external', downloadable=False)
        self.assertFalse(models.installed(self.entry, self.root))
        self.assertFalse(models.inventory(self.root)['models'][0]['active'])
        with self.assertRaisesRegex(ValueError, 'автора'): models.download('test-model', self.root)
        self.entry.update(downloadable=True, gated=True)
        with self.assertRaisesRegex(ValueError, 'автора'): models.download('test-model', self.root)

    def test_shared_dependency_is_counted_at_its_own_pinned_snapshot(self):
        self.files()
        self.entry['files'].append({'path':'codec.json','size':2,'repo':'test/codec','revision':'def456'})
        self.entry['sizeBytes'] += 2
        self.assertFalse(models.installed(self.entry, self.root))
        target=models.file_path(self.entry,self.entry['files'][-1],self.root)
        target.parent.mkdir(parents=True); target.write_bytes(b'{}')
        self.assertTrue(models.installed(self.entry, self.root))
        self.assertIn('models--test--codec',str(target))

    def test_corrupt_or_unknown_saved_selection_uses_known_default(self):
        target = self.root / 'data/studio/models/selection.json'; target.parent.mkdir(parents=True)
        for value in ['not json', '[]', '{"transcription":"arbitrary/repo"}']:
            target.write_text(value)
            self.assertEqual('test-model', models.selections(self.root)['transcription'])

    def test_download_rejects_unknown_ids_and_insufficient_space_without_network(self):
        with self.assertRaises(ValueError): models.download('untrusted/model', self.root)
        with patch.object(models.shutil, 'disk_usage', return_value=type('Disk', (), {'free': 1})()):
            with self.assertRaisesRegex(ValueError, 'места'): models.download('test-model', self.root)

    def test_disk_check_includes_dictionary_expansion_when_weights_are_already_present(self):
        self.files()
        self.entry['resourceBytes'] = 812_000_000
        with patch.object(models.shutil, 'disk_usage', return_value=type('Disk', (), {'free': 500_000_000})()), patch.object(models.model_resources, 'ready', return_value=False):
            with self.assertRaisesRegex(ValueError, 'места'):
                models.download('test-model', self.root)

    def test_only_declared_voice_modes_are_accepted_and_legacy_jobs_keep_defaults(self):
        model={'synthesisMode':'clone','synthesisModes':['clone','design']}
        self.assertEqual('clone',models.synthesis_mode(model,{}))
        self.assertEqual('design',models.synthesis_mode(model,{'voiceMode':'design'}))
        with self.assertRaises(ValueError):models.synthesis_mode(model,{'voiceMode':'preset'})
        with self.assertRaises(ValueError):models.synthesis_mode({'synthesisMode':'clone'},{'voiceMode':'design'})


if __name__ == '__main__': unittest.main()
