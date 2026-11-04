import json,tempfile,unittest,uuid,wave
from pathlib import Path
import numpy as np
from voice_cloner.enhancement import finish,DEFAULTS,RATE,measure,options
ROOT=Path(__file__).resolve().parents[1]
class EnhancementTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);(self.root/'.runtime/bin').mkdir(parents=True);(self.root/'.runtime/bin/ffmpeg').symlink_to(ROOT/'.runtime/bin/ffmpeg')
  self.id=str(uuid.uuid4());self.source=str(uuid.uuid4());self.folder=self.root/'data/studio/inputs'/self.source;self.folder.mkdir(parents=True);(self.root/'data/studio/cleanups').mkdir(parents=True);(self.root/'outputs/studio').mkdir(parents=True)
  t=np.arange(RATE*9)/RATE;self.audio=(np.sin(t*2*np.pi*200)+.4*np.sin(t*2*np.pi*3000))*.15;self.audio[:RATE*3]*=.08;self.audio[round(7.98*RATE):round(8.06*RATE)]=0
  self.before=self.folder/'before.wav';self.write(self.before,self.audio);self.write(self.root/'outputs/studio'/(self.id+'.restored.wav'),self.audio*.7);self.write(self.root/'outputs/studio'/(self.id+'.natural-restored.wav'),self.audio*.7);self.write(self.root/'outputs/studio'/(self.id+'.denoised.wav'),self.audio)
  self.job=dict(id=self.id,sourceId=self.source)
 def tearDown(self):self.temp.cleanup()
 def write(self,path,audio):
  with wave.open(str(path),'wb') as f:f.setparams((1,2,RATE,0,'NONE','not compressed'));f.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())
 def read(self,path):
  with wave.open(str(path),'rb') as f:return np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').copy()
 def run_settings(self,settings):
  (self.root/'data/studio/cleanups'/(self.id+'.json')).write_text(json.dumps(dict(options=settings,baseId=self.id)))
  return finish(self.job,self.root,lambda *_a,**_k:None)
 def test_zero_processing_is_exact_and_source_is_immutable(self):
  original=self.before.read_bytes();output=self.run_settings(dict(strength=0,clarity=0,warmth=0,deEss=0,leveling=False,protectPeaks=False))
  np.testing.assert_array_equal(self.read(output),self.read(self.before));self.assertEqual(self.before.read_bytes(),original)
 def test_mastering_retains_timing_and_cross_chunk_pause_matches_preview_loudness(self):
  output=self.run_settings(DEFAULTS);audio=self.read(output);self.assertEqual(len(audio),len(self.audio));self.assertFalse(np.any(audio[round(7.98*RATE):round(8.06*RATE)]));self.assertLessEqual(np.max(np.abs(audio)),29206)
  first=np.sqrt(np.mean(audio[RATE:RATE*2].astype(float)**2));last=np.sqrt(np.mean(audio[RATE*5:RATE*6].astype(float)**2));self.assertLess(last/first,10)
  a=measure(self.root,['-i',str(output.with_suffix('.compare-before.wav'))],'[0:a]anull')['level'];b=measure(self.root,['-i',str(output.with_suffix('.compare-after.wav'))],'[0:a]anull')['level'];self.assertLess(abs(a-b),.15)
 def test_tone_controls_change_frequency_balance(self):
  neutral=dict(strength=0,clarity=0,warmth=0,deEss=0,leveling=False,protectPeaks=False);a=self.read(self.run_settings(neutral))
  b=self.read(self.run_settings(neutral|dict(clarity=100,warmth=-100)))
  def ratio(x):
   data=x[RATE*4:RATE*5].astype(float);fft=np.abs(np.fft.rfft(data));return fft[3000]/fft[200]
  self.assertGreater(ratio(b)/ratio(a),1.8)
 def test_deesser_reduces_harsh_high_frequency_energy(self):
  t=np.arange(RATE*9)/RATE;a=.06*np.sin(t*2*np.pi*300)+.25*np.sin(t*2*np.pi*8000)
  self.write(self.before,a)
  neutral=dict(strength=0,clarity=0,warmth=0,deEss=0,leveling=False,protectPeaks=False)
  plain=self.read(self.run_settings(neutral));soft=self.read(self.run_settings(neutral|dict(deEss=100)))
  def energy(data,freq):return np.abs(np.fft.rfft(data[RATE:RATE*2].astype(float)))[freq]
  self.assertLess(energy(soft,8000)/energy(plain,8000),.9)
  self.assertGreater(energy(soft,300)/energy(plain,300),.7)
 def test_noise_removal_does_not_depend_on_restoration_strength(self):
  t=np.arange(RATE*9)/RATE;clean=.1*np.sin(t*2*np.pi*300);noise=.04*np.sin(t*2*np.pi*6000)
  self.write(self.before,clean+noise);self.write(self.root/'outputs/studio'/(self.id+'.denoised.wav'),clean);self.write(self.root/'outputs/studio'/(self.id+'.natural-restored.wav'),clean*.8)
  neutral=dict(noiseReduction=100,strength=0,clarity=0,warmth=0,deEss=0,leveling=False,protectPeaks=False)
  def energy(data,freq):return np.abs(np.fft.rfft(data[RATE:RATE*2].astype(float)))[freq]
  raw=self.read(self.before)
  for strength in [0,30,100]:
   processed=self.read(self.run_settings(neutral|dict(strength=strength)))
   self.assertLess(energy(processed,6000),energy(raw,6000)*.005)
   self.assertGreater(energy(processed,300),energy(raw,300)*.9)
  unchanged=self.read(self.run_settings(neutral|dict(noiseReduction=0)))
  np.testing.assert_array_equal(unchanged,raw)
 def test_invalid_settings_are_rejected(self):
  for patch in [dict(noiseReduction=101),dict(strength=101),dict(warmth=float('nan')),dict(deEss=-1),dict(leveling='false')]:
   with self.assertRaises(ValueError):options(patch)
