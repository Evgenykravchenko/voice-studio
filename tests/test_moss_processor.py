from pathlib import Path
import types
import unittest
from unittest.mock import Mock, patch

from voice_cloner.moss_design import load_processor


class MossProcessorTests(unittest.TestCase):
    def test_local_class_resolution_does_not_forward_download_options_to_processor_constructor(self):
        expected = object()
        def native_loader(path, *, codec_path, normalize_inputs):
            self.assertEqual('/local/model', path)
            self.assertEqual('/local/codec', codec_path)
            self.assertFalse(normalize_inputs)
            return expected
        native_class = types.SimpleNamespace(from_pretrained=native_loader)
        resolve = Mock(return_value=native_class)
        module = types.ModuleType('transformers.dynamic_module_utils')
        module.get_class_from_dynamic_module = resolve
        with patch.dict('sys.modules', {'transformers.dynamic_module_utils': module}):
            actual = load_processor(Path('/local/model'), Path('/local/codec'))
        self.assertIs(expected, actual)
        resolve.assert_called_once_with(
            'processing_moss_tts.MossTTSDelayProcessor', '/local/model', local_files_only=True,
        )
