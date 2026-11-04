from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from voice_cloner import synthesis


class QwenReferenceTests(unittest.TestCase):
    def test_long_reference_uses_matching_aligned_audio_and_original_words(self):
        profile={'reference_text':'First original sentence. Last original sentence.','language':'ru'}
        audio=np.linspace(-.2,.2,30*24000,dtype=np.float32);before=audio.copy();calls=[]
        voice=SimpleNamespace(sample_rate=24000)
        def generate(text,**options):
            calls.append((text,options));yield SimpleNamespace(audio=np.array([.1,.2]),sample_rate=24000)
        voice.generate=generate
        core=ModuleType('mlx.core');core.random=SimpleNamespace(seed=lambda _:None);core.array=np.array
        utils=ModuleType('mlx_audio.tts.utils');utils.load_model=lambda *a,**k:voice
        modules={name:ModuleType(name) for name in ['mlx','mlx_audio','mlx_audio.tts']}
        modules.update({'mlx.core':core,'mlx_audio.tts.utils':utils})
        model={'name':'Qwen test','repo':'author/model','adapter':'qwen','runtime':'mlx-audio','synthesisMode':'clone','alignmentRepo':'author/alignment'}
        with patch.dict('sys.modules',modules),patch.object(synthesis,'snapshot',return_value=Path('pinned')),patch.object(synthesis,'component',return_value=Path('alignment')),patch('voice_cloner.reference_alignment.bounded_reference',return_value=('First original sentence.',6.5)) as aligned,patch('voice_cloner.transcription.read_audio',return_value=audio):
            _,run=synthesis.load(model,{'seed':42,'language':'ru'},Path('reference.wav'),profile)
            list(run('Only target words.'));list(run('Next target chunk.'))
        aligned.assert_called_once_with(Path('reference.wav'),profile['reference_text'],'ru',Path('alignment'),model_name='Qwen test',maximum_bytes=2048)
        self.assertEqual(['Only target words.','Next target chunk.'],[t for t,_ in calls])
        for _,options in calls:
            self.assertEqual('First original sentence.',options['ref_text'])
            np.testing.assert_array_equal(audio[:156000],options['ref_audio'])
        np.testing.assert_array_equal(before,audio)
        self.assertEqual('First original sentence. Last original sentence.',profile['reference_text'])
