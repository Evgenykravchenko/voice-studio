import json
import hashlib
import io
import tarfile
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from voice_cloner import runtimes, models


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        (self.root / 'engines').mkdir(); (self.root / 'engines/piper.lock').write_text('piper-tts==1.8.0')
        (self.root / '.runtime/bin').mkdir(parents=True); (self.root / '.runtime/bin/uv').touch()
        python = runtimes.python_for('piper', self.root); python.parent.mkdir(parents=True); python.touch()
        (python.parent.parent/'pyvenv.cfg').write_text('home = '+str(python.parent)+'\n')

    def tearDown(self): self.temp.cleanup()

    def test_readiness_requires_success_and_current_lock(self):
        marker = self.root / '.runtime/engines/piper/ready.json'
        self.assertFalse(runtimes.ready('piper', self.root))
        marker.write_text(json.dumps({'lock':runtimes.signature('piper', self.root)}))
        self.assertTrue(runtimes.ready('piper', self.root))
        (self.root / 'engines/piper.lock').write_text('new lock')
        self.assertFalse(runtimes.ready('piper', self.root))

    def test_failed_import_does_not_mark_runtime_ready(self):
        import subprocess
        with patch.object(runtimes.subprocess,'run',side_effect=[None,None,subprocess.CalledProcessError(1,'probe')]):
            with self.assertRaises(subprocess.CalledProcessError): runtimes.install('piper',self.root)
        self.assertFalse(runtimes.ready('piper',self.root))

    def test_copied_environment_cannot_claim_readiness_from_an_old_checkout(self):
        marker=self.root/'.runtime/engines/piper/ready.json'
        marker.write_text(json.dumps({'lock':runtimes.signature('piper',self.root)}))
        binary=runtimes.python_for('piper',self.root);binary.unlink()
        outside=self.root.parent/(self.root.name+'-old-python');outside.touch()
        try:
            binary.symlink_to(outside)
            self.assertFalse(runtimes.ready('piper',self.root))
        finally:outside.unlink()

    def test_stale_venv_home_is_rejected_even_when_the_executable_was_copied(self):
        binary=runtimes.python_for('piper',self.root)
        (binary.parent.parent/'pyvenv.cfg').write_text('home = /another/checkout/.runtime/python/bin\n')
        self.assertFalse(runtimes.interpreter_local('piper',self.root))

    def test_explicit_qa_environment_symlink_checks_its_real_owner(self):
        alias=self.root/'qa';(alias/'.runtime').mkdir(parents=True)
        (alias/'.runtime/engines').symlink_to(self.root/'.runtime/engines',target_is_directory=True)
        self.assertTrue(runtimes.interpreter_local('piper',alias))

    def test_missing_main_environment_is_not_a_ready_builtin_runtime(self):
        self.assertFalse(runtimes.ready('mlx-speech',self.root))
        binary=self.root/'.venv/bin/python';binary.parent.mkdir(parents=True);binary.touch()
        (binary.parent.parent/'pyvenv.cfg').write_text('home = '+str(binary.parent)+'\n')
        self.assertTrue(runtimes.ready('mlx-speech',self.root))

    def test_all_runtime_caches_and_interpreter_stay_in_project(self):
        with patch.object(runtimes.subprocess,'run') as run:
            runtimes.install('piper',self.root)
        self.assertTrue(runtimes.ready('piper',self.root))
        sync = run.call_args_list[1]
        self.assertEqual(self.root,sync.kwargs['cwd'])
        self.assertIn('--require-hashes',sync.args[0])
        self.assertIn(str(runtimes.python_for('piper',self.root)),sync.args[0])
        for key in ['UV_CACHE_DIR','UV_PYTHON_INSTALL_DIR','HF_HOME','TORCH_HOME','PYTHONPYCACHEPREFIX']:
            self.assertTrue(sync.kwargs['env'][key].startswith(str(self.root)))
        self.assertGreaterEqual(run.call_args_list[-1].kwargs['timeout'],180)

    def test_weights_without_runtime_cannot_be_selected(self):
        entry={'id':'test-piper','name':'Piper','task':'synthesis','integration':'ready','runtime':'piper',
               'repo':'test/repo','revision':'abc','sizeBytes':2,'files':[{'path':'model.onnx','size':2}]}
        target=models.file_path(entry,entry['files'][0],self.root);target.parent.mkdir(parents=True);target.write_bytes(b'xx')
        with patch.object(models,'CATALOG',[entry]),patch.object(models,'DEFAULTS',{'synthesis':'test-piper'}):
            self.assertTrue(models.installed(entry,self.root))
            self.assertFalse(models.inventory(self.root)['models'][0]['active'])
            with self.assertRaises(ValueError): models.select('test-piper',self.root)
            with patch.object(runtimes.subprocess,'run'): runtimes.install('piper',self.root)
            models.select('test-piper',self.root)
            self.assertTrue(models.inventory(self.root)['models'][0]['active'])

    def test_secondary_python_cannot_fall_back_to_a_global_interpreter(self):
        (self.root/'engines/f5.lock').write_text('locked fixture')
        binary=runtimes.python_for('f5',self.root);binary.parent.mkdir(parents=True);binary.touch()
        with patch.object(runtimes.subprocess,'run') as run:
            runtimes.install('f5',self.root)
        command=run.call_args_list[0]
        self.assertIn('--managed-python',command.args[0])
        self.assertEqual('3.11.18',command.args[0][command.args[0].index('--python')+1])
        self.assertEqual(str(self.root/'.runtime/python'),command.kwargs['env']['UV_PYTHON_INSTALL_DIR'])

    def test_source_transfer_retries_without_extracting_the_partial_archive(self):
        output=io.BytesIO()
        with tarfile.open(fileobj=output,mode='w:gz') as archive:
            member=tarfile.TarInfo('fixture/source.py');member.size=4
            archive.addfile(member,io.BytesIO(b'pass'))
        content=output.getvalue()
        source={'url':'https://example.invalid/source.tar.gz','sha256':hashlib.sha256(content).hexdigest(),'directory':'fixture'}
        class Interrupted(io.BytesIO):
            def read(self,size=-1):
                if self.tell():raise TimeoutError('interrupted transfer')
                return super().read(8)
        with patch.object(runtimes,'recipes',return_value={'fixture':source}), patch('urllib.request.urlopen',side_effect=[Interrupted(content),io.BytesIO(content)]) as request, patch('time.sleep') as sleep:
            runtimes.prepare_source('fixture',self.root)
        self.assertEqual(2,request.call_count)
        self.assertEqual(300,request.call_args.kwargs['timeout'])
        sleep.assert_called_once_with(1)
        self.assertEqual('pass',(self.root/'.runtime/sources/fixture/source.py').read_text())
        self.assertFalse((self.root/'.runtime/cache/sources/fixture.tar.part').exists())

    def test_corrupt_source_archive_is_never_extracted(self):
        source={'url':'https://example.invalid/source.tar.gz','sha256':'0'*64,'directory':'fixture'}
        with patch.object(runtimes,'recipes',return_value={'fixture':source}), patch('urllib.request.urlopen',return_value=io.BytesIO(b'corrupt')):
            with self.assertRaisesRegex(ValueError,'Проверка исходников'):
                runtimes.prepare_source('fixture',self.root)
        self.assertFalse((self.root/'.runtime/sources/fixture').exists())
        self.assertFalse((self.root/'.runtime/cache/sources/fixture.tar.part').exists())


if __name__ == '__main__': unittest.main()
