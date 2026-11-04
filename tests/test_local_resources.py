import builtins
import unittest
from unittest.mock import patch
from voice_cloner.local_resources import local_resources

class LocalResourcesTests(unittest.TestCase):
    def test_piper_does_not_require_optional_huggingface_or_transformers_packages(self):
        original = builtins.__import__
        def isolated(name, *args, **kwargs):
            if name.startswith(('huggingface_hub', 'transformers')):
                raise ModuleNotFoundError(name)
            return original(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=isolated):
            with local_resources({'adapter': 'piper'}):
                pass
