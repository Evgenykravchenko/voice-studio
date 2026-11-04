"""Exercise the real optional Torch reader against a tiny legacy-config checkpoint."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from voice_cloner import runtimes

ROOT=Path(__file__).resolve().parents[1]


class XttsCheckpointTests(unittest.TestCase):
    @unittest.skipUnless(runtimes.ready('torch-audio',ROOT),'optional Torch runtime is not installed')
    def test_native_language_splitter_preserves_text_within_model_limits(self):
        env=runtimes.environment(ROOT);env.update(PYTHONPATH=runtimes.module_paths('torch-audio',ROOT),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        program='''from TTS.tts.layers.xtts.tokenizer import VoiceBpeTokenizer
from voice_cloner.xtts_checkpoint import text_parts
from voice_cloner.models import model_for
tokenizer=VoiceBpeTokenizer()
examples={
    'ru':'Сначала проверяем запись. Затем собираем все сцены и сохраняем результат. ',
    'en':'First we check the recording. Then we assemble the scenes and save the result. ',
    'es':'Primero comprobamos la grabación. Después guardamos el resultado. ',
    'fr':'Nous vérifions la prise de son. Ensuite nous enregistrons le résultat. ',
    'de':'Zuerst prüfen wir die Aufnahme. Dann speichern wir das Ergebnis. ',
    'it':'Prima controlliamo la registrazione. Poi salviamo il risultato. ',
    'pt':'Primeiro verificamos a gravação. Depois guardamos o resultado. ',
    'pl':'Najpierw sprawdzamy nagranie. Następnie zapisujemy wynik. ',
    'tr':'Önce kaydı kontrol ediyoruz. Sonra sonucu kaydediyoruz. ',
    'nl':'Eerst controleren we de opname. Daarna slaan we het resultaat op. ',
    'cs':'Nejprve zkontrolujeme nahrávku. Potom uložíme výsledek. ',
    'ar':'نراجع التسجيل أولاً. ثم نحفظ النتيجة. ',
    'hu':'Először ellenőrizzük a felvételt. Ezután mentjük az eredményt. ',
    'ko':'먼저 녹음을 확인합니다. 그런 다음 결과를 저장합니다. ',
    'hi':'पहले हम रिकॉर्डिंग की जाँच करते हैं। फिर परिणाम सहेजते हैं। ',
    'zh':'首先检查录音。然后组合所有场景并保存结果。',
    'ja':'最初に録音を確認します。その後すべての場面をまとめて結果を保存します。',
}
assert set(examples)==set(model_for('xtts-v2')['languages'])
compact=lambda value: ''.join(value.split())
for language,sentence in examples.items():
    limit=tokenizer.char_limits[language]
    for text in (sentence,sentence*12):
        parts=text_parts(text,language,tokenizer)
        assert all(part.strip() and len(part)<=limit for part in parts),(language,parts)
        assert compact(''.join(parts))==compact(text),(language,parts)
        assert all(tokenizer.preprocess_text(part,language).strip() for part in parts)
'''
        result=subprocess.run([str(runtimes.python_for('torch-audio',ROOT)),'-c',program],cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
        self.assertEqual(0,result.returncode,result.stderr[-5000:])

    @unittest.skipUnless(runtimes.ready('torch-audio',ROOT),'optional Torch runtime is not installed')
    def test_legacy_reader_keeps_original_bytes_across_repeated_loads(self):
        folder=ROOT/'.runtime/test-fixtures';folder.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder) as directory:
            env=runtimes.environment(ROOT);env.update(PYTHONPATH=runtimes.module_paths('torch-audio',ROOT),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
            program='''import hashlib,sys,torch
from pathlib import Path
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import _legacy_safe_globals
from voice_cloner.xtts_checkpoint import checkpoint_state
path=Path(sys.argv[1])/'model.pth'
with _legacy_safe_globals():
    torch.save({'config':XttsConfig(),'model':{'probe':torch.tensor([1.,2.])}},path)
digest=hashlib.sha256(path.read_bytes()).hexdigest()
for _ in range(2):
    state=checkpoint_state(path)
    assert torch.equal(state['probe'],torch.tensor([1.,2.]))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
'''
            result=subprocess.run([str(runtimes.python_for('torch-audio',ROOT)),'-c',program,directory],cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
            self.assertEqual(0,result.returncode,result.stderr[-5000:])
