"""Strict, read-only loading of the author's quantized MOSS codec export."""
import json


def codec_weights(weights, arrays):
    result={}
    for key,value in weights.items():
        key=key.replace('.linear1.','.ffn.0.').replace('.linear2.','.ffn.2.')
        key=key.replace('.self_attn.in_projs.0.','.self_attn.in_proj.').replace('.self_attn.out_projs.0.','.self_attn.out_proj.')
        # This export stores fused Conv1d kernels. The native implementation
        # stores weight-normalization parameters in the same source layout.
        if key.startswith('quantizer.') and key.endswith('.weight') and len(value.shape)==3:
            base=key[:-len('weight')]+'parametrizations.weight.'
            norm=arrays.sqrt(arrays.sum(arrays.square(value),axis=(1,2),keepdims=True))
            pairs={base+'original0':norm,base+'original1':arrays.where(norm==0,arrays.ones_like(value),value)}
        else:
            pairs={key:value}
        if result.keys() & pairs.keys():
            raise ValueError('Duplicate MOSS codec parameters after conversion.')
        result.update(pairs)
    return result


def load(path):
    import mlx.core as mx
    import mlx.nn as nn
    from mlx_audio.codec.models.moss_audio_tokenizer.moss_audio_tokenizer import (
        AudioTokenizerConfig, MossAudioTokenizer, _load_weights_from_dir,
    )
    raw=json.loads((path/'config.json').read_text())
    weights=codec_weights(_load_weights_from_dir(path),mx)
    projections={key for key in weights if key.endswith(('.input_proj.weight','.output_proj.weight'))}
    model=MossAudioTokenizer(AudioTokenizerConfig.from_dict(raw),projection_keys=projections)
    if raw.get('quantization'):
        nn.quantize(model,**raw['quantization'],class_predicate=lambda name,module:name+'.scales' in weights)
    model.load_weights(list(weights.items()),strict=True)
    mx.eval(model.parameters())
    model.eval()
    return model
