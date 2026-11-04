# Third-party notices

This file records third-party materials used by Voice Studio. The application code is licensed under [MIT](LICENSE). Existing third-party copyright
notices and license terms are retained separately.

## Compiled frontend

The original notice texts below are included in `frontend/public/licenses/` and copied into
the web build. Package versions come from the installed locked dependency set.

| Component | Version | Original notice |
| --- | --- | --- |
| @fontsource/inter | 5.3.0 | [Inter-OFL-1.1.txt](frontend/public/licenses/Inter-OFL-1.1.txt) |
| react | 19.2.0 | [React-MIT.txt](frontend/public/licenses/React-MIT.txt) |
| react-dom | 19.2.0 | [React-DOM-MIT.txt](frontend/public/licenses/React-DOM-MIT.txt) |
| scheduler | 0.27.0 | [Scheduler-MIT.txt](frontend/public/licenses/Scheduler-MIT.txt) |
| @phosphor-icons/react | 2.1.10 | [Phosphor-MIT.txt](frontend/public/licenses/Phosphor-MIT.txt) |
| vite | 6.4.2 | [Vite-LICENSE.md](frontend/public/licenses/Vite-LICENSE.md) |

## Included inference sources and native wheels

- OpenVoice: MIT; source revision and local modifications are recorded in [vendor/README.md](vendor/README.md), with [original license](vendor/openvoice/LICENSE).
- Resemble Enhance inference sources: MIT; modifications are recorded in [vendor/README.md](vendor/README.md), with [original license](vendor/resemble_enhance/LICENSE).
- OmniVoice rowwise decoder and voice-attribute normalization: Apache-2.0; [source provenance and changes](vendor/omnivoice_rowwise/NOTICE.md), [original license](vendor/omnivoice_rowwise/LICENSE).
- Project-local Hallmark: MIT; [original license](.agents/skills/hallmark/LICENSE) and [disabled integrations/local changes](.agents/skills/hallmark/LOCAL-POLICY.md).
- Native Japanese dependencies and WebRTC VAD: original source archives, license metadata, exact build hashes and the VAD compatibility patch are retained under [engines/wheels](engines/wheels/README.md).

## Installed runtimes and toolchains

Optional runtimes are downloaded into the project using hashed lock files in `engines/`.
Their package license metadata and notices remain in the installed distributions.
Runtime/toolchain binaries and caches are excluded from the source repository.
The build does not combine their licenses into the application code license.

## Model weights and language data

Weights are downloaded or imported explicitly and are excluded from the source repository.
The following entries reproduce the current catalog license labels; each linked author/conversion
model card is the source for its terms. These entries do not grant weight access or relicense models.
The catalog includes restricted and unresolved license labels, as recorded below.
UniDic data for Kokoro, Chatterbox V3 and CosyVoice retains its bundled original notices after installation.

| Catalog entry | Recorded license | Source |
| --- | --- | --- |
| Fish S2 Pro | Fish Audio Research License | [Model card](https://huggingface.co/appautomaton/fishaudio-s2-pro-8bit-mlx) |
| Qwen3-TTS 1.7B Base | apache-2.0 | [Model card](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-Base-4bit) |
| Qwen3-TTS 0.6B Base | apache-2.0; Whisper alignment: MIT | [Model card](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-4bit) |
| Qwen3-TTS 0.6B Base BF16 | apache-2.0 | [Model card](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16) |
| Qwen3-TTS CustomVoice | apache-2.0 | [Model card](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-4bit) |
| Qwen3-TTS VoiceDesign | apache-2.0 | [Model card](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-4bit) |
| Chatterbox Multilingual V3 | mit; UniDic: BSD, LGPL or GPL (bundled licenses) | [Model card](https://huggingface.co/mlx-community/chatterbox-multilingual-v3) |
| Chatterbox Turbo | mit | [Model card](https://huggingface.co/mlx-community/chatterbox-turbo-4bit) |
| CosyVoice 3 | apache-2.0; UniDic: BSD, LGPL or GPL (bundled licenses) | [Model card](https://huggingface.co/mlx-community/Fun-CosyVoice3-0.5B-2512-4bit) |
| VoxCPM2 | apache-2.0 | [Model card](https://huggingface.co/mlx-community/VoxCPM2-4bit) |
| OmniVoice | CC-BY-NC (weights) / Apache-2.0 (code) | [Model card](https://huggingface.co/mlx-community/OmniVoice-4bit) |
| MOSS-TTS | apache-2.0 | [Model card](https://huggingface.co/mlx-community/MOSS-TTS-8B-8bit) |
| MOSS VoiceGenerator | apache-2.0 | [Model card](https://huggingface.co/OpenMOSS-Team/MOSS-VoiceGenerator) |
| FireRedTTS3 Base | apache-2.0 | [Model card](https://huggingface.co/appautomaton/fireredtts3-mlx) |
| XTTS v2 | Coqui Public Model License | [Model card](https://huggingface.co/coqui/XTTS-v2) |
| Kokoro 82M | Apache-2.0 (model); UniDic: BSD, LGPL or GPL (bundled licenses) | [Model card](https://huggingface.co/mlx-community/Kokoro-82M-bf16) |
| Piper — Dmitri | Voice MODEL_CARD / dataset CC0 | [Model card](https://huggingface.co/rhasspy/piper-voices/blob/5041a7a49ae5b3a0f30e6837769eb03fdbb231bd/ru/ru_RU/dmitri/medium/MODEL_CARD) |
| Silero TTS v5.6 RU | CC-BY-NC 4.0 | [Model card](https://github.com/snakers4/silero-models) |
| Piper — Irina | Unknown — see voice MODEL_CARD | [Model card](https://huggingface.co/rhasspy/piper-voices/blob/5041a7a49ae5b3a0f30e6837769eb03fdbb231bd/ru/ru_RU/irina/medium/MODEL_CARD) |
| Piper — Denis | Voice MODEL_CARD / dataset CC0 | [Model card](https://huggingface.co/rhasspy/piper-voices/blob/5041a7a49ae5b3a0f30e6837769eb03fdbb231bd/ru/ru_RU/denis/medium/MODEL_CARD) |
| Piper — Ruslan | Voice MODEL_CARD / dataset CC-BY-NC-SA 4.0 | [Model card](https://huggingface.co/rhasspy/piper-voices/blob/5041a7a49ae5b3a0f30e6837769eb03fdbb231bd/ru/ru_RU/ruslan/medium/MODEL_CARD) |
| F5-TTS v1 Base | cc-by-nc-4.0 | [Model card](https://huggingface.co/lucasnewman/f5-tts-mlx) |
| IndexTTS 2 | Bilibili Model License | [Model card](https://huggingface.co/mlx-community/IndexTTS-2-MLX) |
| VibeVoice 1.5B | mit | [Model card](https://huggingface.co/microsoft/VibeVoice-1.5B) |
| VibeVoice Large | apache-2.0 | [Model card](https://huggingface.co/appautomaton/vibevoice-mlx) |
| LongCat AudioDiT 3.5B | mit | [Model card](https://huggingface.co/appautomaton/longcat-audiodit-3.5b-8bit-mlx) |
| dots.tts SOAR | apache-2.0 | [Model card](https://huggingface.co/appautomaton/dots-tts-mlx) |
| dots.tts MeanFlow | apache-2.0 | [Model card](https://huggingface.co/appautomaton/dots-tts-mlx) |
| Parler-TTS Mini | apache-2.0 | [Model card](https://huggingface.co/parler-tts/parler-tts-mini-v1) |
| Dia 1.6B | apache-2.0; Whisper alignment: MIT | [Model card](https://huggingface.co/mlx-community/Dia-1.6B-4bit) |
| Spark-TTS 0.5B | cc-by-nc-sa-4.0 | [Model card](https://huggingface.co/mlx-community/Spark-TTS-0.5B-4-6bit) |
| Higgs Audio V2 | Boson AI Community License | [Model card](https://huggingface.co/mlx-community/higgs-audio-v2-3B-mlx-q8) |
| Orpheus 3B | apache-2.0 | [Model card](https://huggingface.co/mlx-community/orpheus-3b-0.1-ft-4bit) |
| OpenVoice V2 | mit | [Model card](https://huggingface.co/myshell-ai/OpenVoiceV2) |
| MOSS SoundEffect | apache-2.0 | [Model card](https://huggingface.co/appautomaton/openmoss-sound-effect-mlx) |
| Resemble Enhance | mit | [Model card](https://huggingface.co/ResembleAI/resemble-enhance) |
| Whisper Base | MIT | [Model card](https://huggingface.co/mlx-community/whisper-base-mlx-q4) |
| Whisper Small | MIT | [Model card](https://huggingface.co/mlx-community/whisper-small-mlx-q4) |
| Whisper Large V3 Turbo | MIT | [Model card](https://huggingface.co/mlx-community/whisper-large-v3-turbo-q4) |
| Whisper Medium | MIT | [Model card](https://huggingface.co/mlx-community/whisper-medium-mlx-q4) |
| Whisper Large V3 | MIT | [Model card](https://huggingface.co/mlx-community/whisper-large-v3-mlx-4bit) |
| GigaAM v3 | mit | [Model card](https://huggingface.co/ai-sage/GigaAM-v3) |
| Qwen3-ASR 1.7B | apache-2.0 | [Model card](https://huggingface.co/mlx-community/Qwen3-ASR-1.7B-4bit) |
| Parakeet TDT 0.6B v3 | cc-by-4.0 | [Model card](https://huggingface.co/mlx-community/parakeet-tdt-0.6b-v3) |
| Faster Whisper Large V3 | mit | [Model card](https://huggingface.co/Systran/faster-whisper-large-v3) |
