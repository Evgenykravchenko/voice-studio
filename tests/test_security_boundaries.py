"""Behavioral evidence for the existing CodeQL source-to-sink controls."""
from contextlib import nullcontext
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from voice_cloner import models, runtime_worker, worker


class SecurityBoundaryTests(unittest.TestCase):
    def test_oversize_worker_request_fails_before_model_or_process_access(self):
        engine = worker.Engine()
        with patch.object(worker, 'model_for') as lookup, patch.object(engine, 'external') as external:
            with self.assertRaisesRegex(ValueError, '3000'):
                engine.generate(dict(id='00000000-0000-0000-0000-000000000001', voiceId=None, text='[' * 3001))
        lookup.assert_not_called(); external.assert_not_called()

    def test_unknown_and_option_like_models_cannot_reach_download_or_install(self):
        with patch.object(models, 'direct_download') as download, patch.object(models.runtimes, 'install') as install:
            for value in ('../escape', '/tmp/model', '--root', '--help', 'fish-s2-pro;echo bad', 'fish-s2-pro\n--root'):
                with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Неизвестная'):
                    models.download(value)
        download.assert_not_called(); install.assert_not_called()

    def test_plain_tag_check_and_ssml_reject_entities_before_loading_inference(self):
        import numpy as np
        model = dict(id='test-ssml', task='synthesis', runtime='torch-audio', adapter='silero', markup='ssml',
                     synthesisMode='preset', presetVoices=['test'])
        job = dict(id='00000000-0000-0000-0000-000000000001', modelId=model['id'], text='', seed=1)
        with patch.object(runtime_worker, 'model_for', return_value=model), patch.object(runtime_worker, 'ready', return_value=True), \
             patch('voice_cloner.local_resources.local_resources', return_value=nullcontext()), \
             patch('voice_cloner.synthesis.load', return_value=(24000, lambda text: [np.zeros(24, dtype=np.float32)])) as load, \
             patch.object(runtime_worker, 'save_audio') as save, patch.object(runtime_worker, 'emit'):
            for text in ('<speak><!DOCTYPE speak [<!ENTITY a "bad">]>&a;</speak>', '<speak>&unknown;</speak>'):
                with self.subTest(text=text), self.assertRaises(ValueError): runtime_worker.generate(job | dict(text=text))
            load.assert_not_called(); save.assert_not_called()
            runtime_worker.generate(job | dict(text='<speak>Привет! <break time="100ms"/> Hello.</speak>'))
            load.assert_called_once(); save.assert_called_once()

    def test_model_text_limits_keep_malformed_tags_and_design_input_bounded(self):
        parts = worker.script_parts(('Слово ' + '[' * 25 + ' ') * 50)
        self.assertTrue(parts); self.assertTrue(all(len(text) <= 400 for text, _ in parts))
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'vendor'))
        try:
            from voice_cloner.rowwise import voice_instruction
            self.assertEqual('female, low pitch', voice_instruction('female' + ' ' * 950 + ', low pitch', 'Hello'))
        finally:
            sys.path.pop(0)
