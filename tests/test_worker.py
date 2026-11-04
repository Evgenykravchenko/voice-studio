import unittest
from voice_cloner.worker import script_parts

class ScriptPartsTests(unittest.TestCase):
    def test_pause_becomes_silence_between_exact_fragments(self):
        self.assertEqual(script_parts('Первое. [pause:0.5] Второе.'), [('Первое.', .5), ('Второе.', 0)])
    def test_tags_and_negation_are_preserved(self):
        self.assertEqual(script_parts('[whisper] Я не согласен. То есть, пока не уверен.'), [('[whisper] Я не согласен. То есть, пока не уверен.', 0)])
    def test_invalid_or_excessive_pause_is_rejected(self):
        for text in ['Привет [pause:10]', 'Привет [pause:abc]', '[pause:0.5]']:
            with self.subTest(text=text), self.assertRaises(ValueError): script_parts(text)
    def test_long_text_is_split_without_losing_words(self):
        source = 'Первое предложение. Второе предложение. Третье предложение.'
        parts = script_parts(source, limit=25)
        self.assertEqual(' '.join(speech for speech, _ in parts), source)

if __name__ == '__main__': unittest.main()
