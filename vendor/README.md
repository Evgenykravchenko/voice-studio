# Reviewed inference sources

OmniVoice row-wise INT4/INT8 decoder: extracted without algorithm changes from
ailuntx/OmniVoice-MLX commit21de4138cc8fc0ef88fad2d8e755973ee1982b97, Apache-2.0.
Original copyright/license and source provenance are retained in `omnivoice_rowwise/`.
Packed weights are restored to FP16 at load time as in the conversion author's runtime;
the downloaded files stay unchanged and runtime RAM exceeds the packed model size.

OpenVoice: https://github.com/myshell-ai/OpenVoice/tree/74a1d147b17a8c3092dd5430504bd83ef6c7eb23
MIT, license retained. Only the conversion API is used. Text-cleaner imports are deferred,
and known pinned checkpoints are loaded with explicit torch serialization options.
The optional watermark argument is removed before calling the upstream base constructor.

Resemble Enhance: official PyPI distribution 0.0.1, MIT license retained.
Source: https://github.com/resemble-ai/resemble-enhance
Inference classes are imported directly instead of training entrypoints. Training-only
visualization and unused training/CLI utilities are excluded; network or DeepSpeed
training is not part of this build. Frozen configuration is copied to clear training-only
checkpoint paths. The scalar result of SciPy fsolve is extracted with .item() for NumPy 2
compatibility. Model architecture and inference math are unchanged.
