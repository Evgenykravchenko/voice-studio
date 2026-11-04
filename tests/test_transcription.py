"""Short-utterance GigaAM must not require its optional gated long-form VAD stack."""
from pathlib import Path
import sys
import tempfile
import unittest
from voice_cloner.transcription import load_local_gigaam, validate_language


class FasterWhisperInputTests(unittest.TestCase):
    def test_stereo_recording_is_resampled_before_decoder(self):
        import contextlib
        import types
        from unittest.mock import patch
        import numpy as np
        import soundfile as sf
        from voice_cloner.transcription import transcribe
        received=[]
        class Decoder:
            def __init__(self, *args, **kwargs):
                self.options=kwargs
            def transcribe(self, audio, *, language):
                self.assert_audio(audio, language)
                return iter([types.SimpleNamespace(text=' first '),types.SimpleNamespace(text=' second ')]),None
            def assert_audio(self, audio, language):
                received.append((audio,language,self.options))
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'stereo.wav'
            t=np.arange(48000,dtype=np.float32)/48000
            sf.write(source,np.column_stack([.3*np.sin(2*np.pi*440*t),.1*np.sin(2*np.pi*440*t)]),48000,subtype='FLOAT')
            with patch.dict(sys.modules,{'faster_whisper':types.SimpleNamespace(WhisperModel=Decoder)}),patch('voice_cloner.models.snapshot',return_value=Path(directory)),patch('voice_cloner.local_resources.local_resources',return_value=contextlib.nullcontext()):
                result=transcribe({'adapter':'faster-whisper','runtime':'faster-whisper','languages':['en']},source,'en')
        audio,language,options=received[0]
        self.assertEqual(result,'first second')
        self.assertEqual(audio.shape,(16000,))
        self.assertEqual(audio.dtype,np.float32)
        self.assertTrue(np.all(np.isfinite(audio)))
        self.assertAlmostEqual(float(np.max(audio[100:-100])),.2,places=2)
        self.assertEqual(language,'en')
        self.assertTrue(options['local_files_only'])


class GigaAMLoadingTests(unittest.TestCase):
    def test_unused_optional_vad_import_does_not_prevent_short_utterance_loading(self):
        previous=sys.modules.get('modeling_gigaam')
        try:
            with tempfile.TemporaryDirectory() as directory:
                folder=Path(directory)
                (folder/'modeling_gigaam.py').write_text('''
def longform_only():
    import unavailable_test_vad_package
class GigaAMConfig:
    @classmethod
    def from_pretrained(cls, path, *, local_files_only):
        assert local_files_only
        return {'path':path}
class GigaAMModel:
    @classmethod
    def from_pretrained(cls, path, *, config, local_files_only):
        assert local_files_only and config['path']==path
        return 'local-short-utterance-model'
''')
                self.assertEqual('local-short-utterance-model',load_local_gigaam(folder))
                self.assertNotIn('unavailable_test_vad_package',sys.modules)
        finally:
            if previous is None:sys.modules.pop('modeling_gigaam',None)
            else:sys.modules['modeling_gigaam']=previous

    def test_recording_language_is_checked_before_loading_any_asr(self):
        russian={'languages':['ru']}
        validate_language(russian,'ru'); validate_language(russian,'auto')
        with self.assertRaisesRegex(ValueError,'язык записи'):validate_language(russian,'en')
        validate_language({'languages':['ru','en']},'en')

    def test_bad_author_module_does_not_replace_an_existing_module(self):
        import types
        previous=sys.modules.get('modeling_gigaam');sentinel=types.ModuleType('modeling_gigaam')
        sys.modules['modeling_gigaam']=sentinel
        try:
            with tempfile.TemporaryDirectory() as directory:
                folder=Path(directory);(folder/'modeling_gigaam.py').write_text("raise RuntimeError('invalid local module')")
                with self.assertRaisesRegex(RuntimeError,'invalid local'):load_local_gigaam(folder)
                self.assertIs(sentinel,sys.modules['modeling_gigaam'])
        finally:
            if previous is None:sys.modules.pop('modeling_gigaam',None)
            else:sys.modules['modeling_gigaam']=previous


if __name__=='__main__':unittest.main()
