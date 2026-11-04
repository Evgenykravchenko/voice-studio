from types import SimpleNamespace
import unittest

from voice_cloner.vibevoice_checkpoint import tied_output_weights


class TiedOutputWeightsTests(unittest.TestCase):
    def config(self, tied=True):
        return SimpleNamespace(language_config=SimpleNamespace(tie_word_embeddings=tied))

    def test_missing_output_head_reuses_the_declared_input_tensor_without_mutating_source(self):
        tensor = object(); source = {'model.language_model.embed_tokens.weight': tensor}
        loaded = tied_output_weights(self.config(), source)
        self.assertIs(loaded['lm_head.weight'], tensor)
        self.assertIs(loaded['model.language_model.embed_tokens.weight'], tensor)
        self.assertNotIn('lm_head.weight', source)

    def test_quantized_embedding_groups_are_shared_together(self):
        source = {'model.language_model.embed_tokens.' + suffix: object() for suffix in ('weight', 'scales', 'biases')}
        loaded = tied_output_weights(self.config(), source)
        for suffix in ('weight', 'scales', 'biases'):
            self.assertIs(loaded['lm_head.' + suffix], source['model.language_model.embed_tokens.' + suffix])

    def test_untied_checkpoints_do_not_get_an_invented_output_head(self):
        source = {'model.language_model.embed_tokens.weight': object()}
        self.assertIs(tied_output_weights(self.config(False), source), source)

    def test_an_explicit_output_head_is_not_overwritten(self):
        source = {'model.language_model.embed_tokens.weight': object(), 'lm_head.weight': object()}
        self.assertIs(tied_output_weights(self.config(), source), source)

    def test_a_missing_input_embedding_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'input embedding is missing'):
            tied_output_weights(self.config(), {})


if __name__ == '__main__':
    unittest.main()
