The row-wise tensor decoder is extracted without algorithm changes from
`omnivoice/mlx/omnivoice.py` in https://github.com/ailuntx/OmniVoice-MLX.

- Commit: `21de4138cc8fc0ef88fad2d8e755973ee1982b97`
- Source Git blob: `a504a2945412402e75009b7265b2c3a1069af2a2`
- Copyright 2026 Xiaomi Corp. (authors: Han Zhu).
- License: Apache-2.0, retained in LICENSE.

Voice Studio supplies its existing pinned safetensors bundle. The decoder restores
the author's stored row-wise INT4/INT8 tensors to FP16 for the MLX Audio architecture.
No inference files are written to the weight snapshot. Storage precision does not
describe runtime memory: decoded tensors require more RAM than the packed download.

`voice_design.py` and `_resolve_instruct` in `instructions.py` are also retained
from the same commit, without algorithm changes. Imports are redirected to this
small local package; the Torch inference/training modules are not copied.
