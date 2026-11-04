from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from voice_cloner.japanese import is_japanese, readings


def word(surface, kana=None, pron=None, space=''):
    return SimpleNamespace(surface=surface, white_space=space, feature=SimpleNamespace(kana=kana, pron=pron))


class JapaneseReadingsTests(unittest.TestCase):
    def normalize(self, text, words, **kwargs):
        module = ModuleType('fugashi')
        tagger = Mock(return_value=words)
        module.Tagger = Mock(return_value=tagger)
        with patch.dict('sys.modules', {'fugashi':module}), patch('voice_cloner.model_resources.dictionary', return_value=Path('/local model/dictionary')):
            result = readings(text, {'id':'test'}, **kwargs)
        self.assertIn('"/local model/dictionary"', module.Tagger.call_args.args[0])
        return result

    def test_kanji_becomes_hiragana_without_rewriting_katakana_ascii_spacing_or_punctuation(self):
        text = '今日は スタジオ Java 13。  '
        words = [word('今日','キョウ','キョー'),word('は','ハ','ワ'),word('スタジオ','スタジオ','スタジオ',' '),word('Java','ジャバ','ジャバ',' '),word('13',space=' '),word('。','*','*')]
        self.assertEqual('きょうは スタジオ Java 13。  ', self.normalize(text, words))

    def test_cosyvoice_receives_katakana_pronunciations_with_particles_and_long_vowels(self):
        self.assertEqual('キョーワオンセー。', self.normalize('今日は音声。', [word('今日','キョウ','キョー'),word('は','ハ','ワ'),word('音声','オンセイ','オンセー'),word('。','*','*')], katakana=True))

    def test_unknown_kanji_or_a_tokenizer_that_drops_text_fails_instead_of_losing_words(self):
        with self.assertRaisesRegex(ValueError,'чтение'):
            self.normalize('未知', [word('未知')])
        with self.assertRaisesRegex(ValueError,'потери'):
            self.normalize('未知!', [word('未知','ミチ','ミチ')])

    def test_other_languages_and_already_usable_kana_need_no_dictionary(self):
        self.assertEqual('Java 13! Привет.', readings('Java 13! Привет.', {}))
        self.assertEqual('こんにちは。', readings('こんにちは。', {}))
        self.assertFalse(is_japanese('東京'))
        self.assertFalse(is_japanese('東京の話', 'zh'))
        self.assertTrue(is_japanese('東京', 'ja'))
        self.assertTrue(is_japanese('東京の話'))
