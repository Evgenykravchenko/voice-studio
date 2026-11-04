"""Read the pinned OmniVoice conversion's format without changing its cache files."""
import json
from pathlib import Path


def voice_instruction(description,text):
    from omnivoice_rowwise.instructions import _resolve_instruct
    from omnivoice_rowwise.voice_design import _ZH_RE
    try:
        return _resolve_instruct(description,use_zh=bool(_ZH_RE.search(text))) or 'None'
    except ValueError as exc:
        raise ValueError('Для OmniVoice укажите совместимые атрибуты через запятую, например: female, young adult, low pitch. Нельзя смешивать male и female или несколько значений высоты голоса.') from exc


def read_weights(path):
    import numpy as np
    from safetensors import safe_open
    from omnivoice_rowwise import _dequantize_tensor_np
    path=Path(path)
    quant=json.loads((path/'mlx_manifest.json').read_text())['quantization']
    if quant.get('format')!='omnivoice-rowwise':
        raise ValueError('Неизвестный формат весов OmniVoice. Обновите адаптер модели.')
    tensors=quant['tensors']
    index=json.loads((path/'model.safetensors.index.json').read_text())['weight_map']
    for name in sorted(set(index.values())):
        if Path(name).name!=name:raise ValueError('Некорректный путь к весам OmniVoice.')
        with safe_open(path/name,framework='np') as handle:
            for key in handle.keys():
                if key.endswith('.scales'):continue
                value=_dequantize_tensor_np(handle,key,tensors[key]) if key in tensors else handle.get_tensor(key)
                if np.issubdtype(value.dtype,np.floating):value=value.astype(np.float16)
                yield key,value


def load_omnivoice(path):
    import mlx.core as mx
    from mlx_audio.tts.models.omnivoice import Model,ModelConfig
    path=Path(path)
    config=json.loads((path/'config.json').read_text())
    voice=Model(ModelConfig.from_dict(config))
    weights={key:mx.array(value) for key,value in read_weights(path)}
    voice.load_weights(list(voice.sanitize(weights).items()),strict=True)
    mx.eval(voice.parameters())
    voice.eval()
    return Model.post_load_hook(voice,path)
