# Project-local native dependencies

These are project-built wheels of the unmodified upstream releases:

- `mojimoji`0.0.13, Apache-2.0;
- `pyopenjtalk`0.4.1, with its original license and bundled component notices.

The CosyVoice runtime also includes `webrtcvad`2.0.10+voicestudio.1 (MIT).
Its small, retained compatibility patch replaces the removed `pkg_resources`
metadata lookup with Python's `importlib.metadata`; the native VAD algorithm is
unchanged. The original source archive and exact patch are shipped together.

Upstream provides no Python3.13 macOS ARM64 wheel for these versions. Shipping the
hash-pinned wheels avoids a compiler/Xcode requirement when installing Japanese Kokoro
support. The packages keep the same source versions; model weights and the UniDic3.1
language data are separate artifacts.
WebRTC VAD's upstream release is source-only; its wheel also avoids a compiler
requirement and fixes importing it without the obsolete metadata module.

`manifest.json` records wheel hashes, source hashes and the build-constraint hash.
`source-manifest.json` records official source URLs/hashes; the exact source distributions,
including upstream license notices, are retained in `sources/`. Each wheel also retains
its upstream license metadata. Review those notices before redistribution.

The Japanese wheels target CPython3.13; WebRTC VAD targets the isolated CPython3.11
CosyVoice runtime. All three target ARM64 and macOS14.0. Mach-O load commands were checked
for a14.0 deployment target and system-only linked libraries. This is not a substitute
for testing the supported macOS versions on real hardware.

Maintainers with the macOS compiler tools can rebuild from the project root:

```sh
.venv/bin/python scripts/build-native-wheels.py
# Or rebuild only one artifact:
.venv/bin/python scripts/build-native-wheels.py --packages webrtcvad
```

The build uses `engines/wheel-build.lock`, project-local uv/cache, a fixed source timestamp
and an explicit14.0 deployment target. End users do not run this script. After rebuilding,
review native load commands and update the corresponding hashes in
`mlx-audio-extended.lock` or `cosyvoice.lock`. Run binary-only installation, the
offline runtime probes, actual Japanese generation and a real VAD frame check
before publishing changes.
