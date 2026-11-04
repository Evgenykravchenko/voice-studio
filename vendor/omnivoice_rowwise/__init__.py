# Copyright 2026 Xiaomi Corp. (authors: Han Zhu)
# Licensed under the Apache License, Version 2.0; see LICENSE.
# Extracted from ailuntx/OmniVoice-MLX, omnivoice/mlx/omnivoice.py.
# Kept unmodified; the caller supplies the safetensors handle.
import math
from typing import Any
import numpy as np

def _dequantize_tensor_np(handle, key: str, info: dict[str, Any]) -> np.ndarray:
    bits = int(info["bits"])
    shape = tuple(int(x) for x in info["shape"])
    group_size = int(info["group_size"])
    cols = shape[-1]
    flat_rows = int(np.prod(shape[:-1]))
    groups = math.ceil(cols / group_size)
    scales = handle.get_tensor(f"{key}.scales").astype(np.float32).reshape(flat_rows, groups)

    if bits == 8:
        q = handle.get_tensor(key).astype(np.float32).reshape(flat_rows, groups, group_size)
    elif bits == 4:
        packed = handle.get_tensor(key).reshape(flat_rows, groups, group_size // 2)
        low = (packed & 0x0F).astype(np.int16) - 8
        high = ((packed >> 4) & 0x0F).astype(np.int16) - 8
        q = np.empty((flat_rows, groups, group_size), dtype=np.float32)
        q[:, :, 0::2] = low
        q[:, :, 1::2] = high
    else:
        raise ValueError(f"Unsupported quantization bits: {bits}")

    dequant = (q * scales[:, :, None]).reshape(flat_rows, groups * group_size)
    return dequant[:, :cols].reshape(shape).astype(np.float16)


