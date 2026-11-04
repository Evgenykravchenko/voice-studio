import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from voice_cloner.reference_alignment import alignment_text,select_prefix,bounded_reference


class DiaReferenceTests(unittest.TestCase):
    def test_word_mapping_keeps_original_speaker_markers_and_punctuation(self):
        source=' [S1] First. [S2] Second. Last word.'
        text,positions=alignment_text(source)
        self.assertEqual('First.  Second. Last word.',text)
        self.assertEqual(''.join(source[i] for i in positions),text)
        words=[{'word':'First.','start':0,'end':5.1},{'word':'  Second.','start':5.1,'end':7.2},{'word':' Last','start':7.2,'end':9.8},{'word':' word.','start':9.8,'end':12}]
        self.assertEqual(('[S1] First. [S2] Second.',7.2),select_prefix(source,words))

    def test_without_a_sentence_boundary_only_complete_supplied_words_are_used(self):
        words=[{'word':'one','start':0,'end':5.2},{'word':' two','start':5.2,'end':8},{'word':' three','start':8,'end':12}]
        self.assertEqual(('one two',8),select_prefix('one two three',words))

    def test_mismatched_or_invalid_alignment_cannot_replace_or_drop_source_words(self):
        for words in [[{'word':'invented','start':0,'end':7}], [{'word':'original','start':0,'end':float('nan')}], [{'word':'original','start':8,'end':7}]]:
            with self.assertRaises(ValueError):select_prefix('original',words)

    def test_text_byte_budget_and_missing_useful_boundaries_are_explicit(self):
        words=[{'word':'a'*401,'start':0,'end':7}]
        with self.assertRaisesRegex(ValueError,'короткий образец'):select_prefix('a'*401,words)
        with self.assertRaisesRegex(ValueError,'короткий образец'):select_prefix('word',[{'word':'word','start':0,'end':1}])

    def test_short_reference_bypasses_alignment_and_keeps_exact_supplied_text(self):
        with patch('soundfile.info',return_value=SimpleNamespace(duration=10)):
            self.assertEqual((' [S1] Exact text. ',None),bounded_reference(Path('reference.wav'),' [S1] Exact text. ','en',None))

    def test_missing_bundle_and_oversized_legacy_reference_have_specific_errors_before_model_loading(self):
        with patch('soundfile.info',return_value=SimpleNamespace(duration=30)):
            with self.assertRaisesRegex(ValueError,'установку Dia'):bounded_reference(Path('reference.wav'),'Text.','en',None)
        with patch('soundfile.info',return_value=SimpleNamespace(duration=40)):
            with self.assertRaisesRegex(ValueError,'не более 30 секунд'):bounded_reference(Path('reference.wav'),'Text.','en',None)
