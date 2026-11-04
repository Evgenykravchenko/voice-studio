from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from voice_cloner import synthesis


class OmniVoiceReferenceTests(unittest.TestCase):
    def test_preserves_reference_transcript_and_reuses_encoded_prompt_across_chunks(self):
        calls=[];encodings=[];estimates=[];tokens=SimpleNamespace(shape=(750,8));tokenizer=object()
        profile={'reference_text':'Complete words, including the final sentence.'}
        voice=SimpleNamespace(sample_rate=24000,audio_tokenizer=tokenizer)
        def encode(path,**options):
            encodings.append((path,options));return tokens
        def generate(text,**options):
            calls.append((text,options))
            yield SimpleNamespace(audio=np.array([.1,.2]),sample_rate=24000)
        voice.generate=generate
        core=ModuleType('mlx.core');core.random=SimpleNamespace(seed=lambda value:None)
        utils=ModuleType('mlx_audio.tts.utils');utils.load_model=lambda *a,**k:voice
        prompt=ModuleType('mlx_audio.tts.models.omnivoice.utils');prompt.create_voice_clone_prompt=encode
        class Estimator:
            def estimate_duration(self,*args):estimates.append(args);return 125
        duration=ModuleType('mlx_audio.tts.models.omnivoice.duration');duration.RuleDurationEstimator=Estimator
        modules={name:ModuleType(name) for name in ['mlx','mlx_audio','mlx_audio.tts','mlx_audio.tts.models','mlx_audio.tts.models.omnivoice']}
        modules.update({'mlx.core':core,'mlx_audio.tts.utils':utils,'mlx_audio.tts.models.omnivoice.utils':prompt,'mlx_audio.tts.models.omnivoice.duration':duration})
        with patch.dict('sys.modules',modules),patch.object(synthesis,'snapshot',return_value=Path('pinned')),patch('voice_cloner.rowwise.load_omnivoice',return_value=voice):
            _,run=synthesis.load({'repo':'author/model','adapter':'omnivoice','runtime':'mlx-audio-extended','synthesisMode':'clone'},
                                 {'seed':42,'language':'ru'},Path('reference.wav'),profile)
            list(run('First exact sentence.'));list(run('Second exact sentence.'))
        self.assertEqual([('reference.wav',{'tokenizer':tokenizer,'ref_text':profile['reference_text'],'max_duration_s':30.0})],encodings)
        self.assertEqual(['First exact sentence.','Second exact sentence.'],[text for text,_ in calls])
        for _,options in calls:
            self.assertIs(tokens,options['ref_tokens'])
            self.assertEqual(profile['reference_text'],options['ref_text'])
            self.assertEqual('reference.wav',options['ref_audio'])
            self.assertEqual(5.72,options['duration_s'])
        self.assertEqual([('First exact sentence.',profile['reference_text'],750),('Second exact sentence.',profile['reference_text'],750)],estimates)
        self.assertEqual({'reference_text':'Complete words, including the final sentence.'},profile)
