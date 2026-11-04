import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
from safetensors.numpy import save_file
from voice_cloner.rowwise import read_weights,voice_instruction

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vendor'))


class RowwiseWeightsTests(unittest.TestCase):
    def fixture(self,folder,bits,packed,shape,scale):
        tensors={'matrix.weight':{'bits':bits,'group_size':4,'shape':shape}}
        (folder/'mlx_manifest.json').write_text(json.dumps({'quantization':{'format':'omnivoice-rowwise','tensors':tensors}}))
        (folder/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{'matrix.weight':'model.safetensors'}}))
        save_file({'matrix.weight':packed,'matrix.weight.scales':np.array([[scale]],dtype=np.float32),'norm.weight':np.ones(1,dtype=np.float32)},folder/'model.safetensors')

    def test_int4_signed_nibbles_and_padded_columns_match_the_author_format(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root,4,np.array([[0x08,0xF7]],dtype=np.uint8),[1,3],.5)
            before=(root/'model.safetensors').read_bytes();weights=dict(read_weights(root))
            np.testing.assert_array_equal(weights['matrix.weight'],np.array([[0,-4,-.5]],dtype=np.float16))
            self.assertEqual(np.float16,weights['norm.weight'].dtype)
            self.assertNotIn('matrix.weight.scales',weights)
            self.assertEqual(before,(root/'model.safetensors').read_bytes())

    def test_int8_values_use_their_signed_scale(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root,8,np.array([[-128,-1,0,127]],dtype=np.int8),[1,4],.25)
            np.testing.assert_array_equal(dict(read_weights(root))['matrix.weight'],np.array([[-32,-.25,0,31.75]],dtype=np.float16))

    def test_unknown_bit_format_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root,3,np.array([[1,2]],dtype=np.uint8),[1,4],1)
            with self.assertRaisesRegex(ValueError,'Unsupported quantization bits'):list(read_weights(root))

    def test_voice_attributes_use_author_normalization_and_reject_conflicts(self):
        self.assertEqual('female, low pitch',voice_instruction('FEMALE， LOW PITCH','Hello'))
        self.assertEqual('女，低音调',voice_instruction('female, low pitch','你好'))
        with self.assertRaisesRegex(ValueError,'совместимые атрибуты'):voice_instruction('male, female','Hello')
        with self.assertRaisesRegex(ValueError,'совместимые атрибуты'):voice_instruction('A calm adult speaker','Hello')
