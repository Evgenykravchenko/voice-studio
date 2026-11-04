"""Contracts at the adapter/resource boundary; no weights or network needed."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from voice_cloner import models, runtimes
from voice_cloner.local_resources import local_resources
from voice_cloner.worker import Engine


class ConnectedModelTests(unittest.TestCase):
    def test_every_catalog_entry_has_an_implemented_runtime_and_adapter(self):
        adapters={'fish','qwen','piper','chatterbox','chatterbox-turbo','cosyvoice','voxcpm2','omnivoice','moss','moss-design','firered','kokoro','silero','f5','index','vibevoice-speech','longcat','dots','parler','dia','spark','higgs','orpheus','openvoice','moss-sfx','enhance','xtts','gigaam','qwen-asr','parakeet','faster-whisper','whisper'}
        for entry in models.CATALOG:
            with self.subTest(model=entry['id']):
                self.assertEqual('ready',entry['integration'])
                self.assertIn(entry['adapter'],adapters)
                self.assertIn(entry['runtime'],runtimes.BUILTIN|runtimes.SPECS.keys())
                self.assertTrue(entry['files'])
                if not entry.get('dynamicArtifact'):
                    self.assertEqual(sum(f['size'] for f in entry['files']),entry['sizeBytes'])
                for f in entry['files']:
                    self.assertFalse(Path(f['path']).is_absolute())
                    self.assertNotIn('..',Path(f['path']).parts)
                    if not entry.get('dynamicArtifact'):
                        if f.get('url'):
                            self.assertTrue(f['url'].startswith('https://'))
                            self.assertGreater(f['size'],0)
                            self.assertRegex(f.get('sha256') or '',r'^[a-f0-9]{64}$')
                        else:
                            self.assertRegex(f.get('revision',entry['revision']),r'^[a-f0-9]{40}$')

    def test_additional_languages_reach_the_selected_adapter(self):
        selected={'id':'test-model','task':'synthesis','runtime':'piper'}
        engine=Engine()
        with patch('voice_cloner.worker.model_for',return_value=selected),patch('voice_cloner.worker.ready',return_value=True),patch.object(engine,'unload'),patch.object(engine,'external',return_value={'event':'completed','id':'job'}) as external,patch('voice_cloner.worker.emit'):
            engine.generate({'id':'25a5191d-f278-4dc1-9ef4-158f41693309','modelId':'test-model','voiceId':None,'text':'こんにちは。','language':'ja','emotion':'calm','seed':42})
            self.assertEqual('ja',external.call_args.args[0]['language'])

    def test_local_import_checks_hash_before_readiness(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            entry={'id':'restricted','repo':'author/restricted','revision':'a'*40,'gated':True,'runtime':'piper','sizeBytes':4,'files':[{'path':'model.bin','size':4,'sha256':hashlib.sha256(b'good').hexdigest()}]}
            folder=root/'data/studio/model-imports/restricted';folder.mkdir(parents=True)
            (folder/'model.bin').write_bytes(b'evil')
            with patch.object(models,'CATALOG',[entry]),patch.object(runtimes,'install') as install,patch.object(models,'report'):
                with self.assertRaisesRegex(ValueError,'версии'):models.finish_import('restricted',root)
                install.assert_not_called();self.assertFalse(models.installed(entry,root))
                (folder/'model.bin').write_bytes(b'good')
                models.finish_import('restricted',root)
                install.assert_called_once_with('piper',root)
                self.assertTrue(models.installed(entry,root))
                entry['gated']=False
                with self.assertRaisesRegex(ValueError,'каталога'):models.finish_import('restricted',root)

    def test_untrusted_dynamic_manifest_cannot_mark_a_model_installed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            entry={'id':'dynamic','repo':'author/repo','revision':'v1','artifactSource':'url','dynamicArtifact':True,'files':[{'path':'model.pt','url':'https://example.invalid/model.pt','size':0}]}
            folder=models.snapshot(entry,root);folder.mkdir(parents=True)
            (folder/'manifest.json').write_text('{"size":0,"sha256":"fake"}')
            self.assertFalse(models.installed(entry,root))


class LocalResourceTests(unittest.TestCase):
    def test_only_bundled_resources_resolve_and_patches_are_restored_on_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);weight=root/'weights.bin';weight.write_bytes(b'local')
            hub=types.ModuleType('huggingface_hub');original=lambda *a,**kw:'original'
            hub.hf_hub_download=original;hub.snapshot_download=original
            calls=[]
            class Loader:
                @classmethod
                def from_pretrained(cls,path,**kwargs):calls.append((path,kwargs));return 'loaded'
            transformers=types.ModuleType('transformers')
            transformer_utils=types.ModuleType('transformers.utils');transformer_utils.is_torch_available=lambda:True
            for name in ['AutoTokenizer','AutoProcessor','AutoFeatureExtractor','AutoModel','AutoConfig','PreTrainedModel']:
                setattr(transformers,name,type(name,(Loader,),{}))
            entry={'repo':'author/main','revision':'a','files':[{'path':'weights.bin','size':5}],'resourceAliases':{'old/repo':'author/main'}}
            with patch.dict(sys.modules,{'huggingface_hub':hub,'transformers':transformers,'transformers.utils':transformer_utils}),patch('voice_cloner.local_resources.snapshot',return_value=root),patch('voice_cloner.local_resources.file_path',return_value=weight):
                with self.assertRaisesRegex(RuntimeError,'failure'):
                    with local_resources(entry):
                        self.assertEqual(str(weight),hub.hf_hub_download('old/repo','weights.bin'))
                        self.assertEqual(str(root),hub.snapshot_download('old/repo'))
                        with self.assertRaises(FileNotFoundError):hub.hf_hub_download('arbitrary/repo','weights.bin')
                        with self.assertRaises(FileNotFoundError):hub.snapshot_download('arbitrary/repo')
                        transformers.AutoTokenizer.from_pretrained('old/repo')
                        self.assertEqual((root,{'local_files_only':True}),calls[-1])
                        raise RuntimeError('failure')
                self.assertIs(original,hub.hf_hub_download)
                self.assertEqual('loaded',transformers.AutoTokenizer.from_pretrained('old/repo'))
                self.assertEqual(('old/repo',{}),calls[-1])



class CompatibilityGuardTests(unittest.TestCase):
    def test_mlx_only_runtime_does_not_require_pytorch(self):
        hub=types.ModuleType('huggingface_hub');hub.hf_hub_download=lambda *a,**k:None;hub.snapshot_download=hub.hf_hub_download
        transformers=types.ModuleType('transformers');utils=types.ModuleType('transformers.utils');utils.is_torch_available=lambda:False
        class Loader:
            @classmethod
            def from_pretrained(cls,path,**kwargs):return path,kwargs
        for name in ['AutoTokenizer','AutoProcessor','AutoFeatureExtractor','AutoConfig']:setattr(transformers,name,type(name,(Loader,),{}))
        model={'repo':'author/model','revision':'abc','files':[]}
        with patch.dict(sys.modules,{'huggingface_hub':hub,'transformers':transformers,'transformers.utils':utils}),patch('voice_cloner.local_resources.snapshot',return_value=Path('/pinned/local')):
            with local_resources(model):
                self.assertEqual((Path('/pinned/local'),{'local_files_only':True}),transformers.AutoTokenizer.from_pretrained('author/model'))

    def test_f5_rejects_unsupported_reference_before_loading_weights(self):
        from voice_cloner import runtime_worker
        entry={'id':'f5-tts','runtime':'f5','adapter':'f5','referenceLanguages':['en','zh']}
        profile={'language':'ru','reference_text':'Привет, это русский эталон.'}
        with patch.object(runtime_worker,'model_for',return_value=entry),patch.object(runtime_worker,'ready',return_value=True),patch.object(runtime_worker,'_load_profile',return_value=(profile,Path('unused.wav'))):
            with self.assertRaisesRegex(ValueError,'английском'):runtime_worker.generate({'id':'qa','modelId':'f5-tts','voiceId':'qa','text':'Hello.'})

if __name__=='__main__':unittest.main()
