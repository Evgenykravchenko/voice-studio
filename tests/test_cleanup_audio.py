import array,hashlib,math,tempfile,unittest,wave
from pathlib import Path
import numpy as np
from voice_cloner.cleanup_audio import restore_file,retain_source_silence,RATE
class CleanupAudioTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.before=self.root/'before.wav';self.samples=np.sin(np.arange(RATE)*2*np.pi*440/RATE).astype(np.float32)*.2;self.samples[RATE//5:RATE*2//5]=0
  with wave.open(str(self.before),'wb') as f:f.setparams((1,2,RATE,0,'NONE','not compressed'));f.writeframes((self.samples*32767).astype('<i2').tobytes())
  self.hash=hashlib.sha256(self.before.read_bytes()).hexdigest()
 def tearDown(self):self.tmp.cleanup()
 def test_streamed_overlap_preserves_length_silence_and_original(self):
  sizes=[];progress=[]
  def enhance(a):sizes.append(len(a));return a*.5
  out=self.root/'after.wav';restore_file(self.before,self.before,out,enhance,lambda i,n:progress.append((i,n)),hop_seconds=.08,overlap_seconds=.02,context_seconds=.01)
  with wave.open(str(out),'rb') as f:
   self.assertEqual(f.getnframes(),RATE);actual=np.frombuffer(f.readframes(RATE),dtype='<i2')
  self.assertTrue(np.all(actual[RATE//5:RATE*2//5]==0));self.assertLess(max(sizes),RATE*.13);self.assertEqual(progress[-1][0],progress[-1][1]);self.assertEqual(hashlib.sha256(self.before.read_bytes()).hexdigest(),self.hash)
  self.assertLess(np.max(np.abs(actual-self.samples*32767*.5)),2)
 def test_model_cannot_fill_deliberate_silence(self):
  out=self.root/'after.wav';restore_file(self.before,self.before,out,lambda a:a+.1,lambda *_:None,hop_seconds=.1)
  with wave.open(str(out),'rb') as f:actual=np.frombuffer(f.readframes(RATE),dtype='<i2')
  self.assertTrue(np.all(actual[RATE//5:RATE*2//5]==0))
 def test_wrong_length_fails_without_publishing_result(self):
  out=self.root/'after.wav'
  with self.assertRaises(ValueError):restore_file(self.before,self.before,out,lambda a:a[:-1],lambda *_:None)
  self.assertFalse(out.exists());self.assertFalse(out.with_suffix('.tmp').exists());self.assertEqual(hashlib.sha256(self.before.read_bytes()).hexdigest(),self.hash)
 def test_resampling_cannot_leave_ringing_inside_an_editor_gap(self):
  source=self.root/'source';converted=self.root/'converted.wav'
  # Stereo48k master becomes mono44.1k for enhancement. Both channels define silence.
  samples=np.full((48000,2),5000,dtype='<i2');samples[9600:24000]=0
  with wave.open(str(source),'wb') as f:f.setparams((2,2,48000,0,'NONE','not compressed'));f.writeframes(samples.tobytes())
  original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
  resampled=np.full(RATE,3000,dtype='<i2')
  with wave.open(str(converted),'wb') as f:f.setparams((1,2,RATE,0,'NONE','not compressed'));f.writeframes(resampled.tobytes())
  retain_source_silence(source,converted)
  with wave.open(str(converted),'rb') as f:
   self.assertEqual(RATE,f.getnframes());actual=np.frombuffer(f.readframes(RATE),dtype='<i2')
  self.assertTrue(np.all(actual[8820:22050]==0));self.assertTrue(np.all(actual[:8820]==3000));self.assertTrue(np.all(actual[22050:]==3000))
  self.assertEqual(original_hash,hashlib.sha256(source.read_bytes()).hexdigest())
 def test_compressed_input_keeps_the_validated_conversion(self):
  source=self.root/'compressed';source.write_bytes(b'compressed fixture')
  retain_source_silence(source,self.before)
  self.assertEqual(hashlib.sha256(self.before.read_bytes()).hexdigest(),self.hash)
