# Models and delivery

**English** · [Русский](models.ru.md) · [Home](../README.md)

## Choose by task

The catalog contains **45 entries**, including **33 synthesis variants**. A
model is the downloadable system that performs a task. A voice profile is your
small reference recording and transcript; it is not another set of model weights.

| You want to… | Look for |
| --- | --- |
| Clone a voice | Fish S2 Pro, Qwen Base, Chatterbox, CosyVoice, VoxCPM2 and other cloning models. |
| Use built-in speakers | Piper, Silero, Kokoro, Qwen CustomVoice or Orpheus. |
| Describe a new voice | Qwen VoiceDesign, MOSS VoiceGenerator, Parler, or description mode in VoxCPM2/OmniVoice. Spark uses voice parameters. |
| Prepare a sample transcript | Whisper, GigaAM, Qwen-ASR, Parakeet or Faster Whisper. |
| Improve recorded speech | Resemble Enhance in Audio enhancement. |
| Change a recording's voice | OpenVoice V2 with a target profile. |
| Generate a sound | MOSS SoundEffect with a description and duration. |

Use the language, capability and task filters. Not every model supports Russian:
Piper and Silero offer Russian speakers; Kokoro does not. F5's reference recording
must be English or Chinese. Each card describes the connected integration.

OmniVoice's description mode expects supported English/Chinese attributes, such
as `female, young adult, low pitch`, rather than unrestricted Russian prose.
Do not combine conflicting attributes. Spark offers voice type, pitch and speed
instead of a free-text description.

## Install and select

Open Models, install a model and wait for readiness. The app downloads pinned
files, checks them, prepares its isolated runtime and any required language data.
Only fully ready models can be selected. Cancel retains partial download data so
you can continue later; a failed installation can be retried.

Choose the synthesis model in Speech. Choose an ASR model in Models before preparing
a new voice. Changes apply to new tasks; existing takes keep their model and settings.
Models are not downloaded just by browsing their cards.

## Delivery and pauses

For a first test, use ordinary text and the model's available delivery selector.
There is no universal emotion syntax:

| Family | Example or control |
| --- | --- |
| Fish | `[whisper] A quiet sentence.` or `[laughing] That was unexpected.` |
| Chatterbox Turbo | `[sigh]` and `[chuckle]`; English speech. |
| Orpheus | `<sigh>` and `<laugh>`; English speech. |
| Dia | `[S1]` / `[S2]` dialogue markers and supported nonverbal notes. |
| Qwen CustomVoice/VoiceDesign, VoxCPM2, IndexTTS 2 | Use the supported delivery controls. |
| Silero | SSML inside `<speak>…</speak>`; `+` before a stressed vowel. |
| Other families | Follow the editor hint; foreign tags may be rejected. |

`[pause:0.5]` inserts half a second of silence in ordinary text. Silero SSML has
its own pause syntax, for example `<break time="500ms"/>`. Do not mix the two formats.
Emotions are guidance, not a guarantee of acting strength. Keep the reference
transcript literal, without emotion tags that were not spoken.

Fish infers language from text and uses a fixed temperature of 0.8. Chatterbox
Multilingual and XTTS need an explicit speech language. Interface language does
not select or translate the spoken language.

A saved seed helps compare generations; it does not guarantee identical audio
across models, library versions or execution paths.

## Memory and storage

Download size is **not RAM usage**. The card includes required artifacts; separate
runtime packages, caches and extracted dictionaries need additional space.

| Example | Download, approximately | Observed peak RSS |
| --- | ---: | ---: |
| Piper Dmitri | 0.06 GB | 0.21 GiB |
| Silero RU | 0.15 GB | 1.00–1.01 GiB |
| Whisper Small | 0.20 GB | 0.55 GiB |
| Resemble Enhance | 0.71 GB | 6.15–6.19 GiB |
| Fish S2 Pro | 6.73 GB | 6.12–9.56 GiB |

Only the current task loads its model; jobs are serialized. You do not need all
45 models on disk. The published measurements used a 36 GiB Apple Silicon Mac;
8 GB machines were not separately certified. RSS is an observed process peak,
not a minimum RAM requirement; macOS, Java, the browser and full GPU memory are
not included. See the [complete measurements](model-resources.md).

Some models have extra costs: OmniVoice's INT4 weights are expanded to FP16 at
runtime; Japanese dictionaries for Kokoro, Chatterbox and CosyVoice need about
812 MB of additional extracted data per model.

## Quality and licenses

Use a clean reference, short sentences and a supported language. Listen to the
result before sharing it. All catalog entries completed control tasks, but longer
text, stress, mixed languages and voice similarity can vary. VibeVoice Large can
repeat words from some short references; aggressive enhancement can alter speech.
See [quality notes](model-quality.md) and [verification status](release-status.md).

The app's MIT license does not relicense model weights. Read the model card's
license before using it in your intended setting.

[Using the studio](guide.md) · [Troubleshooting](troubleshooting.md)
