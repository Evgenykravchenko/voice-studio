from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from voice_cloner import synthesis
from voice_cloner.moss_codec import codec_weights


class MossCodecTests(unittest.TestCase):
    def test_nested_pinned_codec_directory_is_passed_to_native_reference_encoder_and_decoder(self):
        calls=[]
        voice=SimpleNamespace(sample_rate=24000)
        def generate(text, **options):
            calls.append(options)
            yield SimpleNamespace(audio=np.array([.1,.2]),sample_rate=24000)
        voice.generate=generate
        core=ModuleType('mlx.core');core.random=SimpleNamespace(seed=lambda value:None)
        utils=ModuleType('mlx_audio.tts.utils');utils.load_model=lambda *a,**k:voice
        modules={name:ModuleType(name) for name in ['mlx','mlx_audio','mlx_audio.tts']}
        modules.update({'mlx.core':core,'mlx_audio.tts.utils':utils})
        model={'repo':'author/model','adapter':'moss','runtime':'mlx-audio-extended','synthesisMode':'clone','codecRepo':'author/codec','codecSubdir':'mlx-int8','files':[{'repo':'author/codec','path':'mlx-int8/config.json'}]}
        codec=object()
        with patch.dict('sys.modules',modules),patch('voice_cloner.moss_codec.load',return_value=codec) as load_codec,patch.object(synthesis,'snapshot',return_value=Path('/local/model')),patch.object(synthesis,'file_path',return_value=Path('/local/codec/mlx-int8/config.json')):
            rate, synthesize=synthesis.load(model,{'seed':42},Path('reference.wav'),{'reference_text':'Exact reference.'})
            list(synthesize('Test sentence.'))
        self.assertEqual(24000,rate)
        self.assertEqual('/local/codec/mlx-int8',calls[0]['audio_tokenizer_source'])
        self.assertEqual('Exact reference.',calls[0]['ref_text'])
        self.assertIs(codec,voice.audio_tokenizer)
        load_codec.assert_called_once_with(Path('/local/codec/mlx-int8'))

    def test_quantized_weight_names_keep_scale_and_bias_groups_aligned(self):
        w=np.ones((2,2));values={f'decoder.0.transformer.layers.0.linear1.{suffix}':w for suffix in ['weight','scales','biases']}
        renamed=codec_weights(values,np)
        self.assertEqual({f'decoder.0.transformer.layers.0.ffn.0.{suffix}' for suffix in ['weight','scales','biases']},set(renamed))
        self.assertTrue(all(v is w for v in renamed.values()))

    def test_fused_convolution_reparameterization_preserves_values_and_zero_rows(self):
        kernel=np.array([[[1.],[2.]],[[0.],[0.]]],dtype=np.float32)
        result=codec_weights({'quantizer.input_proj.weight':kernel},np)
        g=result['quantizer.input_proj.parametrizations.weight.original0'];v=result['quantizer.input_proj.parametrizations.weight.original1']
        restored=g*v/np.sqrt(np.sum(v*v,axis=(1,2),keepdims=True))
        np.testing.assert_allclose(kernel,restored,atol=1e-6)
        self.assertTrue(np.isfinite(restored).all())

    def test_conflicting_export_names_are_rejected_instead_of_overwriting_parameters(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            codec_weights({'layer.linear1.weight':np.ones((1,1)),'layer.ffn.0.weight':np.ones((1,1))},np)
