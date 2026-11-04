import array
import hashlib
import math
from pathlib import Path
import tempfile
import unittest
import wave
from voice_cloner.assembly import render, RATE
ROOT=Path(__file__).resolve().parents[1]

class AssemblyTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.runtime'); self.root=Path(self.temp.name)
  (self.root/'.runtime/bin').mkdir(parents=True); (self.root/'.runtime/bin/ffmpeg').symlink_to(ROOT/'.runtime/bin/ffmpeg')
  (self.root/'outputs/studio').mkdir(parents=True)
  self.source=self.root/'outputs/studio/source.wav'
  data=array.array('h',(int(math.sin(i*2*math.pi*400/RATE)*3000) for i in range(RATE*2)))
  with wave.open(str(self.source),'wb') as f:f.setparams((1,2,RATE,0,'NONE','not compressed'));f.writeframes(data.tobytes())
  self.original=hashlib.sha256(self.source.read_bytes()).hexdigest()
 def tearDown(self):self.temp.cleanup()
 def clip(self,**kwargs):return {'sceneId':'scene-a','sourceId':'test','path':str(self.source),'start':.2,'end':1.2,'gap':.3,'gainDb':0,**kwargs}
 def test_trim_gap_spans_formats_and_original_survive(self):
  out=self.root/'result'; result=render({'clips':[self.clip(),self.clip(sceneId='scene-b',start=.5,end=1.25,gainDb=-3)],'leveling':True,'softEdges':True},out,self.root)
  self.assertAlmostEqual(result['duration'],2.05,places=4)
  self.assertAlmostEqual(result['spans'][1]['start'],1.3,places=4)
  self.assertAlmostEqual(result['spans'][0]['trimStart'],.2)
  with wave.open(str(out/'master.wav'),'rb') as f:
   self.assertEqual(f.getframerate(),RATE); f.setpos(RATE);self.assertEqual(set(f.readframes(round(RATE*.3))),{0})
  self.assertGreater((out/'master.mp3').stat().st_size,1000)
  self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.original)
  self.assertTrue(result['peaks']);self.assertTrue((out/'result.json').exists())
 def test_last_pause_is_omitted_and_leveling_is_optional(self):
  result=render({'clips':[self.clip(gap=4)],'leveling':False,'softEdges':False},self.root/'one',self.root)
  self.assertAlmostEqual(result['duration'],1,places=4);self.assertEqual(result['spans'][0]['appliedGainDb'],0)
 def test_invalid_ranges_and_external_paths_fail(self):
  for clip in (self.clip(end=.21),self.clip(start=-1),self.clip(end=5),self.clip(path=str(ROOT/'frontend/public/audio/scene-1.wav')),self.clip(gainDb=float('nan'))):
   with self.subTest(clip=clip),self.assertRaises(ValueError):render({'clips':[clip],'leveling':True,'softEdges':True},self.root/'invalid',self.root)
