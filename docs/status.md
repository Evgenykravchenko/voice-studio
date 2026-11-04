# Release status

**English** · [Русский](status.ru.md) · [Home](../README.md)

Voice Studio **0.1.0 runs locally on macOS 14+ with Apple Silicon**. Windows, Linux,
Intel Macs and CUDA deployment are not currently supported by the installer.

## Verified

- All 45 catalog entries completed real control tasks, including a run with independently downloaded weights and UI workflows.
- Voice preparation, synthesis, conversion, effects, cleanup, saving, playback and seeking were exercised in isolated test data.
- Project persistence, take selection, montage and export have automated and browser checks.
- The source publication excludes personal files, environments and weights.

These checks used an Apple Silicon Mac with 36 GiB memory. They do not certify
every language, recording, long script or other computer. A fresh installation
contains no model weights, voice profiles or personal projects.

## Known limits

Speech models can mispronounce words, stress, numbers or mixed-language terms.
Cloning similarity and emotion strength vary. VibeVoice Large can repeat parts
of short references. Strong audio restoration can change words or timbre.
Listen before sharing a result and retain its source.

Public internet hosting and multi-user accounts are outside the current local
application's scope. Single-model removal is not exposed in the interface yet.
Windows/Linux need separate runtime integration and testing.

Detailed historical evidence is retained in the [technical audit](release-status.md)
and [quality notes](model-quality.md), currently in Russian. Large test copies
were removed after verification; retained reports describe those historical runs.

[Model guide](models.md) · [Troubleshooting](troubleshooting.md)
