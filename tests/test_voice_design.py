import itertools
import unittest
from voice_cloner.voice_design import spark_options,spark_global_phase,SPARK_LEVELS


class SparkVoiceTests(unittest.TestCase):
    def test_codec_grammar_only_constrains_its_fixed_speaker_code_segment(self):
        start,end=90,91
        self.assertIsNone(spark_global_phase([1,2,3],start,end))
        self.assertEqual('codes',spark_global_phase([1,start],start,end))
        self.assertEqual('codes',spark_global_phase([1,start]+[5]*31,start,end))
        self.assertEqual('end',spark_global_phase([1,start]+[5]*32,start,end))
        self.assertIsNone(spark_global_phase([1,start]+[5]*32+[end,7],start,end))
        self.assertEqual('codes',spark_global_phase([start,5,end,start,5],start,end))

    def test_every_discrete_setting_maps_to_native_control(self):
        for gender,pitch,speed in itertools.product(['male','female'],SPARK_LEVELS,SPARK_LEVELS):
            with self.subTest(gender=gender,pitch=pitch,speed=speed):
                self.assertEqual({'gender':gender,'pitch':SPARK_LEVELS[pitch],'speed':SPARK_LEVELS[speed]},spark_options(f'{gender}, {pitch} pitch, {speed} speed'))

    def test_arbitrary_description_cannot_silently_become_a_default_voice(self):
        for description in ['',None,'A warm voice','male, 1.3 pitch, low speed','female, low pitch, moderate speed, extra']:
            with self.subTest(description=description):
                with self.assertRaisesRegex(ValueError,'тип, высоту и темп'):spark_options(description)
