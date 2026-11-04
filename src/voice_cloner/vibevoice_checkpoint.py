"""Strict local loading of VibeVoice checkpoints, including tied output embeddings."""
from dataclasses import replace


def tied_output_weights(config, weights):
    if not config.language_config.tie_word_embeddings or 'lm_head.weight' in weights:
        return weights
    source = 'model.language_model.embed_tokens.'
    if source + 'weight' not in weights:
        raise ValueError('VibeVoice declares tied embeddings but the input embedding is missing.')
    # Reuse existing checkpoint tensors; never initialize a missing output head
    # randomly or weaken strict shape/key validation. Quantization groups also tie.
    return weights | {'lm_head.' + suffix: weights[source + suffix]
                      for suffix in ('weight', 'scales', 'biases') if source + suffix in weights}


def load(path):
    import mlx.core as mx
    from mlx_speech.models.vibevoice.checkpoint import (
        LoadedVibeVoiceModel, get_quantization_config, load_checkpoint_into_model,
        load_vibevoice_checkpoint, quantize_vibevoice_model, resolve_vibevoice_model_dir,
    )
    from mlx_speech.models.vibevoice.model import VibeVoiceForConditionalGeneration
    class ConsistentLanguageInputs(VibeVoiceForConditionalGeneration):
        def lm_forward(self, *, inputs_embeds, cache=None):
            # Speech diffusion yields float32 features; text embeddings may be
            # bfloat16. The language KV cache must keep one value dtype per job.
            return super().lm_forward(inputs_embeds=inputs_embeds.astype(self._language_input_dtype), cache=cache)
    resolved = resolve_vibevoice_model_dir(path)
    checkpoint = load_vibevoice_checkpoint(resolved)
    weights = tied_output_weights(checkpoint.config, checkpoint.state_dict)
    if weights is not checkpoint.state_dict:
        checkpoint = replace(checkpoint, state_dict=weights)
    model = ConsistentLanguageInputs(checkpoint.config)
    quantization = get_quantization_config(checkpoint.config)
    if quantization is not None:
        quantize_vibevoice_model(model, quantization, state_dict=weights)
    alignment = load_checkpoint_into_model(model, checkpoint, strict=True)
    model._language_input_dtype = model.embed_tokens(mx.array([0])).dtype
    return LoadedVibeVoiceModel(model_dir=resolved, config=checkpoint.config, model=model,
                                checkpoint=checkpoint, alignment_report=alignment, quantization=quantization)
