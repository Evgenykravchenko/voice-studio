import unittest

from voice_cloner.dia_prompt import cloning_prompt


class DiaPromptTests(unittest.TestCase):
    def test_plain_reference_and_script_form_one_speaker_turn_with_an_end_marker(self):
        self.assertEqual(cloning_prompt('A clear reference.', 'The complete final sentence.'),
                         ('[S1] A clear reference.', 'The complete final sentence. [S2]'))

    def test_cloned_speaker_tag_is_not_repeated_at_the_reference_boundary(self):
        self.assertEqual(cloning_prompt('[s1] A clear reference.', '[S1] The next sentence.'),
                         ('[S1] A clear reference.', 'The next sentence. [S2]'))

    def test_dialogue_keeps_all_words_and_speaker_changes(self):
        self.assertEqual(cloning_prompt('A clear reference.', '[S1] First turn. [S2] Second turn.'),
                         ('[S1] A clear reference.', 'First turn. [S2] Second turn. [S1]'))
        self.assertEqual(cloning_prompt('A clear reference.', '[S2] Another speaker. [S1]'),
                         ('[S1] A clear reference.', '[S2] Another speaker. [S1]'))

    def test_empty_inputs_are_rejected(self):
        for reference, text in [('', 'Words.'), ('Reference.', '')]:
            with self.subTest(reference=reference, text=text), self.assertRaises(ValueError):
                cloning_prompt(reference, text)


if __name__ == '__main__':
    unittest.main()
