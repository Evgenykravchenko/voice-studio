from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import unittest
from unittest.mock import patch

import numpy as np
from voice_cloner import synthesis


class CosyVoicePromptTests(unittest.TestCase):
    def test_native_zero_shot_boundary_is_added_without_changing_the_saved_transcript(self):
        for transcript in ['A clear reference.', 'You are a helpful assistant.<|endofprompt|>A clear reference.']:
            with self.subTest(transcript=transcript):
                calls=[]
                class Voice:
                    sample_rate=24000
                    def __init__(self, config): pass
                    def generate(self, text, **options):
                        calls.append((text, options))
                        yield SimpleNamespace(audio=np.array([.1,.2],dtype=np.float32),sample_rate=24000)
                core=ModuleType('mlx.core');core.random=SimpleNamespace(seed=lambda value:None)
                utils=ModuleType('mlx_audio.tts.utils');utils.load_model=lambda *a,**k:None
                cosy=ModuleType('mlx_audio.tts.models.cosyvoice3');cosy.Model=Voice;cosy.ModelConfig=lambda **kwargs:kwargs
                modules={name:ModuleType(name)for name in ['mlx','mlx_audio','mlx_audio.tts','mlx_audio.tts.models']}
                modules.update({'mlx.core':core,'mlx_audio.tts.utils':utils,'mlx_audio.tts.models.cosyvoice3':cosy})
                profile={'reference_text':transcript}
                with patch.dict(sys.modules,modules),patch('voice_cloner.synthesis.snapshot',return_value=Path('pinned')),patch('voice_cloner.transcription.read_audio',return_value=np.ones(24,dtype=np.float32)):
                    rate, generate=synthesis.load({'adapter':'cosyvoice','runtime':'cosyvoice','synthesisMode':'clone'}, {'seed':42},Path('reference.wav'),profile)
                    self.assertEqual(24000,rate);list(generate('The target sentence.'))
                self.assertEqual('The target sentence.',calls[0][0])
                self.assertEqual('You are a helpful assistant.<|endofprompt|>A clear reference.',calls[0][1]['ref_text'])
                self.assertIsNone(calls[0][1]['stt_model'])
                self.assertEqual(transcript,profile['reference_text'])


if __name__=='__main__':
    unittest.main()
