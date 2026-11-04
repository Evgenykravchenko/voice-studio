# Optional local runtimes

The model catalog is an allowlist of pinned Hugging Face revisions and required files.
`integration: ready` means an adapter exists; `ready` in the inventory additionally requires
verified model files and a successfully installed runtime. Downloading weights alone never
makes an unsupported model selectable.

Each optional runtime is installed by the project-local uv into `.runtime/engines/<name>`.
Its checked-in `.lock` pins transitive package versions and distribution hashes.
Install uses `uv pip sync --require-hashes`; a successful import writes a marker tied to
the lock's SHA-256. Failure/cancellation leaves it unready and can be retried. Installation
and download subprocesses, including their descendants, are stopped on cancellation/shutdown.
Caches and managed interpreters stay in `.runtime`. No global pip, uv tools or shell profile edits.
Internet is required for installation; inference sets Hugging Face/Transformers offline mode.

Java freezes the requested model before queuing. A single Python worker serializes ASR and
synthesis. Fish retains its existing environment and idle unload. Optional runtimes run in
one isolated child per generation; completion is returned after the child exits, releasing
its entire model. This costs a model load per job but avoids keeping multiple families in RAM.

Runtime groups (all dependencies and Python versions are isolated):

- Base Python 3.13 / MLX Speech: Fish, FireRed, VibeVoice, LongCat, dots.tts, MOSS SFX;
  MLX Whisper remains available for ASR.
- `mlx-audio`: Qwen3-TTS, Qwen3-ASR, Parakeet.
- `mlx-audio-extended`: Chatterbox, VoxCPM2, OmniVoice, MOSS TTS, Kokoro,
  Dia, Spark, Higgs, Orpheus. Bundles include the required codecs/tokenizers.
- `cosyvoice`: MLX Audio Plus overlay, isolated from the main MLX Audio namespace.
- `f5`: F5-TTS MLX and Vocos; `index`: pinned MLX IndexTTS source.
- `torch-audio`: XTTS, Silero, OpenVoice, Resemble Enhance, GigaAM.
- `parler`: separate older Transformers ABI; `moss`: Transformers 5 for MOSS VoiceGenerator.
- `faster-whisper`: CTranslate2 CPU INT8 ASR.
- `piper`: compact ONNX preset voices with bundled espeak-ng.

Legacy runtimes use their own Python 3.11 under `.runtime/python`; the main Python 3.13
and existing CLI environment stay unchanged. `sources.json` pins tarball revisions and
SHA-256 for source-only adapters. Checked-in `vendor/` contains reviewed MIT conversion
and enhancement sources with licenses and a modification record.

`local_resources.py` restricts secondary HF lookups to the current model's pinned bundle.
Unexpected dependencies fail offline. Large PyTorch runtimes run on CPU on macOS and
can require considerably more RAM than their weight-file size. A catalog adapter and
successful import probe are not an end-to-end quality certificate for every weight variant.

Model/voice licenses are separate from runtime licenses and appear in each catalog card.
Piper has no cloning, emotion instruction or reproducible-seed control in this integration.
Qwen Base uses the reference recording and transcript; its emotion instruction is unsupported.
Qwen CustomVoice and VoiceDesign use an instruction rather than Fish's bracketed tags.
Language support and voice similarity vary by model; do not promise identical quality.

XTTS uses Coqui's sentence splitter with the checkpoint's per-language character
limits before decoding. Its spaCy/Japanese dependencies and Chinese Pypinyin frontend
are included in the hashed Torch lock. The import probe exercises Russian splitting
and Japanese/Chinese preprocessing offline; no spaCy model download is needed.

To update a runtime, review its source and regenerate its lock using the project-local uv,
then test actual inference. A changed lock invalidates the old readiness marker.
