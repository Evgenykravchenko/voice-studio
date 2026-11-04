from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from voice_cloner import synthesis


class TurboReferenceTests(unittest.TestCase):
    def prepare(self, audio):
        calls=[]
        voice=SimpleNamespace(sample_rate=24000)
        def generate(text,**options):
            calls.append(options)
            yield SimpleNamespace(audio=np.array([.1,.2]),sample_rate=24000)
        voice.generate=generate
        core=ModuleType('mlx.core');core.random=SimpleNamespace(seed=lambda value:None)
        utils=ModuleType('mlx_audio.tts.utils');utils.load_model=lambda *a,**k:voice
        modules={name:ModuleType(name) for name in ['mlx','mlx_audio','mlx_audio.tts']}
        modules.update({'mlx.core':core,'mlx_audio.tts.utils':utils})
        with patch.dict('sys.modules',modules),patch.object(synthesis,'snapshot',return_value=Path('pinned')),patch('voice_cloner.transcription.read_audio',return_value=audio):
            _,run=synthesis.load({'repo':'author/model','adapter':'chatterbox-turbo','runtime':'mlx-audio-extended','synthesisMode':'clone'},{'seed':42},Path('reference.wav'),{'reference_text':'Exact reference.'})
            list(run('Test sentence.'))
        return calls[0]

    def test_exact_minimum_adds_only_one_silent_sample_in_memory(self):
        audio=np.linspace(-.2,.2,5*24000,dtype=np.float32);original=audio.copy()
        options=self.prepare(audio)
        np.testing.assert_array_equal(original,audio)
        np.testing.assert_array_equal(original,options['ref_audio'][:-1])
        self.assertEqual(0,options['ref_audio'][-1]);self.assertEqual(120001,len(options['ref_audio']))
        self.assertEqual(24000,options['sample_rate'])

    def test_longer_reference_retains_native_path_and_shorter_legacy_reference_has_a_clear_error(self):
        self.assertEqual('reference.wav',self.prepare(np.zeros(30*24000,dtype=np.float32))['ref_audio'])
        with self.assertRaisesRegex(ValueError,'не менее 5 секунд'):
            self.prepare(np.zeros(4*24000,dtype=np.float32))
