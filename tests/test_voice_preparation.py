import array
from contextlib import nullcontext
import math
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import uuid
import wave

from voice_cloner import worker


class VoicePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.id = str(uuid.uuid4())
        self.directory = self.root / 'data/studio/voice-imports' / self.id
        self.directory.mkdir(parents=True)
        self.job = {'id': self.id, 'start': 0, 'duration': 5, 'language': 'ru'}
        self.root_patch = patch.object(worker, 'PROJECT_DIR', self.root)
        self.emit_patch = patch.object(worker, 'emit')
        self.root_patch.start()
        self.events = self.emit_patch.start()
        self.asr = {'id':'test-asr','task':'transcription','runtime':'mlx-whisper','languages':['ru','en'],
                    'repo':'test/asr','revision':'a'*40,'files':[]}
        self.model_patch=patch.object(worker,'model_for',return_value=self.asr)
        self.ready_patch=patch.object(worker,'ready',return_value=True)
        self.selection_patch=patch.object(worker,'selections',return_value={'transcription':'test-asr'})
        self.resources_patch=patch('voice_cloner.local_resources.local_resources',return_value=nullcontext())
        self.model_patch.start();self.ready_patch.start();self.selection_patch.start();self.resources_patch.start()

    def tearDown(self):
        self.resources_patch.stop();self.selection_patch.stop();self.ready_patch.stop();self.model_patch.stop()
        self.emit_patch.stop()
        self.root_patch.stop()
        self.temporary.cleanup()

    def audio(self, duration=5, amplitude=0.1):
        samples = array.array('h', (round(amplitude * 32767 * math.sin(i * 0.1)) for i in range(round(44100 * duration))))
        with wave.open(str(self.directory / 'source'), 'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(44100)
            audio.writeframes(samples.tobytes())

    def test_silence_short_excerpt_and_corrupt_file_are_rejected_before_asr(self):
        engine = worker.Engine()
        self.audio(amplitude=0)
        with self.assertRaisesRegex(ValueError, 'тихая'):
            engine.prepare_voice(self.job)
        self.audio(duration=0.3)
        with self.assertRaisesRegex(ValueError, 'меньше 5'):
            engine.prepare_voice(self.job)
        (self.directory / 'source').write_text('not audio')
        with self.assertRaisesRegex(ValueError, 'прочитать запись'):
            engine.prepare_voice(self.job)

    def test_reference_is_mono_pcm_and_models_are_released_before_and_after_asr(self):
        self.audio()
        engine = worker.Engine()
        engine.model = object()
        engine.references['old'] = object()
        holder = types.SimpleNamespace(model=object())
        def transcribe(path, **kwargs):
            self.assertIsNone(engine.model)
            self.assertFalse(engine.references)
            with wave.open(path, 'rb') as audio:
                self.assertEqual((1, 2, 44100), (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()))
            self.assertEqual('ru', kwargs['language'])
            return {'text': '  Точная речь!  '}
        fake = types.ModuleType('mlx_whisper')
        fake.transcribe = transcribe
        sub = types.ModuleType('mlx_whisper.transcribe')
        sub.ModelHolder = holder
        with patch.dict('sys.modules', {'mlx_whisper': fake, 'mlx_whisper.transcribe': sub}), patch.object(worker, 'selected_path', return_value='test-asr-model'):
            engine.prepare_voice(self.job)
        self.assertIsNone(holder.model)
        self.assertEqual('completed', self.events.call_args.args[0])
        self.assertEqual('Точная речь!', self.events.call_args.kwargs['transcript'])
        self.assertAlmostEqual(5, self.events.call_args.kwargs['duration'])

    def test_invalid_ranges_do_not_run_ffmpeg(self):
        with patch.object(worker.subprocess, 'run') as run:
            for start, duration in [(float('nan'), 5), (0, float('inf')), (-1, 10), (0, 31), (0, 4)]:
                with self.assertRaises(ValueError):
                    worker.Engine().prepare_voice({**self.job, 'start': start, 'duration': duration})
            run.assert_not_called()

    def test_supported_japanese_recording_reaches_its_frozen_recognizer(self):
        self.audio()
        self.asr.update(languages=['ja'], runtime='mlx-audio')
        engine = worker.Engine()
        with patch.object(engine, 'external', return_value={'transcript':'こんにちは。'}) as transcribe:
            engine.prepare_voice({**self.job, 'language':'ja', 'modelId':'japanese-recognizer'})
        self.assertEqual('ja', transcribe.call_args.args[0]['language'])
        self.assertEqual(self.asr['id'], transcribe.call_args.args[0]['modelId'])
        self.assertEqual('こんにちは。', self.events.call_args.kwargs['transcript'])

    def test_malformed_language_is_rejected_before_selection_or_conversion(self):
        with patch.object(worker, 'model_for') as select, patch.object(worker.subprocess, 'run') as run:
            for language in [None, '', '../ja', 'Japanese', 'ja\n', ['ja']]:
                with self.assertRaisesRegex(ValueError, 'язык записи'):
                    worker.Engine().prepare_voice({**self.job, 'language':language})
            select.assert_not_called()
            run.assert_not_called()

    def test_recording_uses_its_frozen_recognizer_and_rejects_an_unsupported_language_before_conversion(self):
        self.asr['languages']=['ru']
        with patch.object(worker,'model_for',return_value=self.asr) as choose,patch.object(worker,'selections') as selection,patch.object(worker.subprocess,'run') as conversion:
            with self.assertRaisesRegex(ValueError,'язык записи'):
                worker.Engine().prepare_voice({**self.job,'language':'en','modelId':'frozen-recognizer'})
            choose.assert_called_once_with('frozen-recognizer')
            selection.assert_not_called();conversion.assert_not_called()
