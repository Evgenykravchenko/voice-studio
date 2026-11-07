# Changelog

**English** · [Русский](CHANGELOG.ru.md) · [Home](README.md)

## 0.1.1 - 2026-11-07

- Fix first-time setup failing with `spawnSync pnpm ENOENT` when no global pnpm is installed ([#6](https://github.com/Evgenykravchenko/voice-studio/issues/6)).
- Use the pinned project's Node.js and pnpm ESM entry point for frontend installation and builds, including nested dependency checks.
- Add regression checks for a clean environment, paths with spaces and missing local tools. No global package installation is required.

Existing users: update the project source following the [update guide](docs/storage.md), stop a running studio and run `./scripts/studio.sh` again. Keep your data and models.

## 0.1.0 - 2026-11-04

First release of the local Voice Studio for macOS 14+ on Apple Silicon.

- Generate speech using a cloned, built-in or described voice, depending on the model.
- Create reusable voice profiles from recordings and review their transcripts.
- Download selected models from a catalog of 45 entries with isolated local runtimes.
- Assemble scenes with drag and drop, takes, waveform trimming, gain and pauses; export WAV or MP3.
- Record or upload audio for noise removal and voice restoration, with before/after comparison.
- Keep projects, takes, profiles and processing history locally, with English/Russian UI and light/dark themes.
- Install the required tools through the project launcher; model weights are downloaded separately.

Repository changes require PRs, CI and Conventional Commits. Release tags and
published assets are protected. Vite includes the 6.4.5 security patches.
The 138 existing CodeQL signals were individually traced and did not establish
an exploitable path in the supported deployment; regression tests preserve the
relevant controls. See [security review](docs/security-review.md).

This is an ordinary `v0.1.0` release, not a snapshot. It does not add Windows,
Linux, Intel Mac, public hosting or multi-user support. Speech quality and memory
requirements depend on the model. See [release status](docs/status.md) and [setup](docs/setup.md).
