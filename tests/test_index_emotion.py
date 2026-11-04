"""Index's exposed delivery must reach the native model, without pretending to support others."""
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
import numpy as np
from voice_cloner import models
from voice_cloner.synthesis import load


class IndexEmotionTests(unittest.TestCase):
    def boundary(self):
        calls=[]
        class Voice:
            def __init__(self,**kwargs):calls.append(('load',kwargs))
            def generate(self,**kwargs):calls.append(('generate',kwargs));return np.ones(24,dtype=np.float32)
        module=types.ModuleType('mlx_indextts.generate_v2');module.IndexTTSv2=Voice
        return calls,patch.dict(sys.modules,{'mlx_indextts':types.ModuleType('mlx_indextts'),'mlx_indextts.generate_v2':module})

    def test_selected_delivery_reaches_native_generation_with_original_text_and_seed(self):
        model=models.model_for('index-tts2');text='We can continue. Do not change this sentence.'
        for delivery,native in [('calm',None),('excited','happy'),('angry','angry')]:
            calls,boundary=self.boundary()
            with boundary,patch('voice_cloner.synthesis.snapshot',return_value=Path('/qa/model')):
                rate,synth=load(model,{'seed':42,'emotion':delivery,'language':'en'},Path('/qa/reference.wav'),{'reference_text':'A reference.'})
                list(synth(text))
            self.assertEqual(rate,22050)
            request=calls[-1][1];self.assertEqual(request['emotion'],native);self.assertEqual(request['text'],text);self.assertEqual(request['seed'],42);self.assertEqual(request['reference_audio'],'/qa/reference.wav')

    def test_unsupported_delivery_fails_before_loading_large_weights(self):
        for delivery in ['whisper','laughing']:
            calls,boundary=self.boundary()
            with boundary,patch('voice_cloner.synthesis.snapshot',return_value=Path('/qa/model')):
                with self.assertRaisesRegex(ValueError,'поддерживает подачу'):
                    load(models.model_for('index-tts2'),{'seed':42,'emotion':delivery},Path('/qa/reference.wav'),{})
            self.assertEqual(calls,[])
