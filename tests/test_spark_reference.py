from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from voice_cloner import synthesis


class SparkReferenceTests(unittest.TestCase):
    def test_cloning_uses_native_speaker_conditioning_without_changing_profile_or_target(self):
        calls=[];profile={'reference_text':'The complete reference transcript.'}
        voice=SimpleNamespace(sample_rate=16000,eval=lambda:None,_audio_tokenizer=SimpleNamespace(model=SimpleNamespace(eval=lambda:None),feature_extractor=SimpleNamespace(eval=lambda:None)))
        def generate(text,**options):
            calls.append((text,options))
            yield SimpleNamespace(audio=np.array([.1,.2]),sample_rate=16000)
        voice.generate=generate
        core=ModuleType('mlx.core');core.random=SimpleNamespace(seed=lambda value:None)
        utils=ModuleType('mlx_audio.tts.utils');utils.load_model=lambda *a,**k:voice
        modules={name:ModuleType(name) for name in ['mlx','mlx_audio','mlx_audio.tts']}
        modules.update({'mlx.core':core,'mlx_audio.tts.utils':utils})
        with patch.dict('sys.modules',modules),patch.object(synthesis,'snapshot',return_value=Path('pinned')):
            _,run=synthesis.load({'repo':'author/model','adapter':'spark','runtime':'mlx-audio-extended','synthesisMode':'clone'},{'seed':42},Path('reference.wav'),profile)
            list(run('Exact target sentence.'))
        self.assertEqual('Exact target sentence.',calls[0][0])
        self.assertEqual('reference.wav',calls[0][1]['ref_audio'])
        self.assertIsNone(calls[0][1]['ref_text'])
        self.assertEqual({'reference_text':'The complete reference transcript.'},profile)
