# Production readiness audit

Status: **in progress: not release approved** (2026-10-31, local date).

Current consolidated evidence: [release-status.md](release-status.md). Historical checkpoints below may be superseded.
The current catalog has 45 entries: OpenAudio S1 Mini was removed at the user's
explicit request on 2026-11-02. Earlier 46-model matrices remain historical evidence.

Objective: verify every catalog model and every application workflow for a fresh installation.
Adapter presence, import probes and mocked tests are not inference evidence. A test on one
Apple Silicon Mac does not establish Windows/Linux/NVIDIA support, low-memory compatibility,
all languages, arbitrary recordings or commercial rights.

| Requirement | Required evidence | Status |
| --- | --- | --- |
| Every model download/import | Actual pinned files/hashes, cancel/resume/retry, network/disk errors | In progress |
| Every model's advertised task | Real inference, valid output, quality/transcript review, controls, repeat run | Pending |
| Fresh installation | Empty caches, one documented setup path, locked local Java/Node/Python/FFmpeg | Pending |
| Studio | Clone/preset/design, language/markup, queue/errors/retry, takes, playback/seek/volume, immutable source | Pending |
| Voice profiles | Upload, every ASR, edit/save, search/pagination/delete, in-use protection | Pending |
| Projects | New/open/import/export, restart, offline backup, conflicts, migration, audio links | Pending |
| Montage | Drag order, cuts/reset/undo, gain, gaps/exclusion, WAV/MP3, preview/export parity | Pending |
| Enhancement/conversion/effects | File/mic, capture lifecycle, comparison, versions, scene/master apply, real outputs | Pending |
| Catalog | All filters, install/select/import/cancel/retry, actual progress, compatibility | Pending |
| UI | All tabs, RU/EN, dark/light, responsive, keyboard, loading/empty/error/offline | Current release regression pending |
| Resources | Serialized inference, child termination, timeout/idle unload, bounded RAM/disk, restart | Pending |
| Release | Anonymous assets/source, ignored personal data, accurate docs/licenses, packaging/startup | Pending |
| Platforms | Actual tests on every advertised OS/architecture; clear unsupported cases | Apple Silicon only documented; other hardware unverified |

Evidence scripts: `scripts/verify-catalog.py` (read-only inventory, optional author manifests and
local hashes) and `scripts/verify-runtimes.py` (offline import probes). Raw JSON/logs and generated
media stay in ignored `.runtime/release-audit/`. Neither script certifies inference or release.
All UI mutation tests require an isolated API/data root; never change saved user projects.
Do not bypass author license/access gates. Unsupported hardware must not be advertised as tested.

Initial host: Apple Silicon,36GiB unified memory. Catalog:46 entries,13 installed;134.14GB of
listed files before deduplicating shared dependencies, excluding runtimes and dynamic Silero.

## Per-model evidence

| Model | Task | Runtime | Files present initially | Actual inference in this audit |
| --- | --- | --- | --- | --- |
| fish-s2-pro | synthesis | mlx-speech | yes | technical smoke passed; quality pending |
| qwen3-base-1-7b | synthesis | mlx-audio | no | technical smoke passed; quality pending |
| qwen3-base-0-6b | synthesis | mlx-audio | yes | technical smoke passed; quality pending |
| qwen3-base-0-6b-bf16 | synthesis | mlx-audio | yes | technical smoke passed; quality pending |
| qwen3-customvoice | synthesis | mlx-audio | no | technical smoke passed; quality pending |
| qwen3-voicedesign | synthesis | mlx-audio | no | technical smoke passed; quality pending |
| chatterbox-v3 | synthesis | mlx-audio-extended | no | root/fresh Russian and Japanese smoke passed after offline readings; broader quality pending |
| chatterbox-turbo | synthesis | mlx-audio-extended | no | technical smoke passed; quality pending |
| cosyvoice3 | synthesis | cosyvoice | no | native prompt boundary fixed; root/fresh short and UI exact; long missing phrase restored, only е/ё ASR differences remain |
| voxcpm2 | synthesis | mlx-audio-extended | no | technical smoke passed; quality pending |
| omnivoice | synthesis | mlx-audio-extended | no | technical smoke passed; quality pending |
| moss-tts | synthesis | mlx-audio-extended | no | root/fresh short and UI/long technical passed; broader quality pending |
| moss-voicegenerator | synthesis | moss | no | root/fresh short and UI/long technical passed; long fidelity review |
| fireredtts3 | synthesis | mlx-speech | no | root/fresh technical smoke passed; quality pending |
| xtts-v2 | synthesis | torch-audio | no | repaired root repeat and fresh technical smoke passed; quality pending |
| kokoro | synthesis | mlx-audio-extended | yes | technical smoke passed; quality pending |
| piper-dmitri | synthesis | piper | yes | technical smoke passed; quality pending |
| silero-v5-ru | synthesis | torch-audio | no | pending |
| piper-irina | synthesis | piper | yes | technical smoke passed; quality pending |
| piper-denis | synthesis | piper | yes | technical smoke passed; quality pending |
| piper-ruslan | synthesis | piper | yes | technical smoke passed; quality pending |
| f5-tts | synthesis | f5 | yes | technical smoke passed; quality pending |
| index-tts2 | synthesis | index | no | root/fresh and compiled UI passed technically; short and long phrases screened exactly |
| vibevoice-1-5b | synthesis | mlx-speech | no | repaired root/fresh, UI and long synthesis passed; short/UI/long phrases screened exactly |
| vibevoice-large-mlx | synthesis | mlx-speech | no | repaired root/fresh, UI and long synthesis passed; 5s reference repeats source words, confirmed by two ASRs; quality issue remains open |
| longcat | synthesis | mlx-speech | no | root/fresh and compiled UI technical checks passed; both short phrases screened exactly |
| dots-soar | synthesis | mlx-speech | no | repaired root/fresh technical smoke passed; quality pending |
| dots-mf | synthesis | mlx-speech | no | root/fresh technical smoke passed; quality pending |
| parler-mini | synthesis | parler | no | root/fresh and compiled UI passed technically; another UI phrase omitted words, independent ASR review pending |
| dia-1-6b | synthesis | mlx-audio-extended | no | context-format fix passed root/fresh short, UI and root long; intended short/UI/long text recovered exactly |
| spark-tts | synthesis | mlx-audio-extended | no | technical smoke passed; quality pending |
| higgs-v2 | synthesis | mlx-audio-extended | no | root/fresh, UI and long technical checks passed; short/UI exact, long ASR mismatch requires review |
| orpheus-3b | synthesis | mlx-audio-extended | no | technical smoke passed; quality pending |
| openaudio-s1-mini | synthesis | fish-legacy | no | pending |
| openvoice-v2 | conversion | torch-audio | yes | technical smoke passed; quality pending |
| moss-sfx | processing | mlx-speech | no | root/fresh effects and exact duration passed; full UI/browser download passed |
| resemble-enhance | processing | torch-audio | yes | technical smoke passed; quality pending |
| whisper-base | transcription | mlx-whisper | yes | technical smoke passed; quality pending |
| whisper-small | transcription | mlx-whisper | yes | technical smoke passed; quality pending |
| whisper-turbo | transcription | mlx-whisper | no | technical smoke passed; quality pending |
| whisper-medium | transcription | mlx-whisper | no | technical smoke passed; quality pending |
| whisper-large-v3 | transcription | mlx-whisper | no | technical smoke passed; quality pending |
| gigaam-v3 | transcription | torch-audio | no | technical smoke passed; quality pending |
| qwen3-asr | transcription | mlx-audio | no | technical smoke passed; quality pending |
| parakeet-v3 | transcription | mlx-audio | no | technical smoke passed; quality pending |
| faster-whisper-v3 | transcription | faster-whisper | no | technical smoke passed; quality pending |

## Current checkpoint (supersedes historical counts below)

- 32 synthesis variants have passed actual UI generation/playback/persistence checks and
  technical long-text/chunk/pause scenarios. These are not all-language quality certifications.

- 44 distinct catalog variants have completed real short tasks in both the working and
  independently installed fresh runtimes. Weights were reused for the fresh inference;
  the separate empty-cache Piper install remains the fresh weight-download evidence.
- XTTS initially produced valid audio but its upstream loader rewrote the pinned checkpoint.
  Original author weights were re-downloaded; the read-only loader passed two root runs
  (30.41s/29.8s) and a fresh-runtime repeat (32.69s). No pinned artifact changed, readiness
  remained true and the original full SHA256 was verified after all three runs.
- Faster Whisper initially failed in the PyAV file decoder. The shared mono/16 kHz
  loader and a locked SciPy dependency now bypass that incompatible call. Real Russian ASR
  passed in both root and fresh runtimes (18.0s and18.11s). Stereo/resampling regression passed.
- Latest completed suites:105 Python,59 frontend and39 Java
  tests. These counts cover application contracts, not arbitrary model quality.
- Qwen CustomVoice generated all9 catalog presets and Orpheus all8, with distinct output
  hashes. Local ASR recovered their short phrases closely. All54 fresh Kokoro presets generated;
  zf_xiaoni still needs Mandarin listening review. ASR agreement is not perceptual certification.
  Under the stricter exact-normalized-text rule below, Qwen has8 exact screens and Eric requires
  review; Orpheus has8 exact screens. Fresh Kokoro has48 exact screens and6 review cases
  (hf_alpha, hf_beta, hm_omega, hm_psi, jm_kumo, zf_xiaoni). Some disagreements may be recognizer
  spelling/orthography; they are not silently treated as proven synthesis failures or passes.
- VoxCPM2 and OmniVoice now expose clone/design modes. Actual compiled UI generation without
  profiles passed, including immutable submitted settings, project/job persistence, restart,
  playback and responsive checks in RU/dark and EN/light. Omni instructions use the author's
  supported English/Chinese voice attributes and reject conflicts before loading weights.
- OmniVoice's pinned bundle uses custom rowwise INT4, not ordinary MLX quantization. Its
  adapter follows the conversion author's retained Apache-licensed decoder, loads strictly,
  and expands to FP16. Packed file size must not be presented as peak memory. Cloning keeps
  the complete reference excerpt aligned with its transcript; root/fresh generation passed.
- CosyVoice now uses the shared PCM reader; root/fresh synthesis and transcript screening
  passed. Parakeet explicitly selects its architecture because snapshot directories are hashes;
  root/fresh Russian ASR passed, as did the Qwen-ASR regression.
- Spark controlled generation initially failed because the quantized model emitted ordinary
  text in its fixed32-token speaker-code segment. The adapter now constrains that segment
  to model-sampled valid codec IDs and its closing marker; no missing code is padded or invented.
  Both female/high and male/low cases generated in the fresh runtime, with exact short phrase
  ASR screening. Compiled UI generation without profiles, immutable settings and reload passed.
  A visual review caught truncated control values; compact label/value rows now show full
  selections and fit1280x720. Twelve RU/dark and EN/light viewport checks from320 to1366px
  passed with no clipped values, overflow or default inspector scrolling. A separate Hallmark
  finish reviewer returned ship with no actionable findings. Static lint had0 FAIL and two
  existing answered warnings; the Hallmark render tier was unavailable. Real screenshots
  came from Playwright, not that render tier.
- Chatterbox Multilingual completed installation and real root/fresh Russian cloning
  (12.8s/11.39s); local ASR matched the short phrase. A Japanese cross-language sample
  generated valid audio but ASR agreement was only.5301 and requires further investigation;
  it is not counted as a passed Japanese quality check. Following the author's cross-language
  guidance (`cfg_weight=0` for a known language mismatch) improved ASR agreement to.6585,
  but the case still requires review. A second independent Qwen-ASR screen agreed only.8148
  with the intended text and also found changed words. Native v3 text preprocessing was retained.
  No advertised model was dropped.
- Inference verifiers now check artifact size/mtime and readiness after each run, failing if
  inference changes pinned weights. The XTTS fault demonstrates why valid audio alone is insufficient.
- The old main download runner terminated. XTTS restoration completed; two disjoint retry
  batches remain active for retained partials and the remaining large models. The runner now measures idle log activity with a monotonic clock;
  wall-clock changes no longer create false idle timeouts. No duplicate model downloads are launched.
- Japanese models and all five Kokoro Japanese presets remain in scope; their fresh generation
  and compiler-free dependency evidence are retained. The user revoked the request to skip them.
- FireRedTTS3 completed actual installation and root/fresh synthesis (14.89s/16.59s).
  Its local transcript screen matched the phrase exactly. Dots SOAR first rejected the generic
  2048-token budget: its native API caps audio patches at512. The family-specific cap and
  native None automatic language fixed this. Root/fresh synthesis passed (21.98s/21.06s),
  artifact readiness remained intact, and its English phrase matched the ASR screen exactly.
- Language controls were reconciled with actual adapters: Chatterbox and XTTS require an
  explicit target language; F5, CosyVoice and Index infer it from text, like VoxCPM2 and Spark.
  This prevents displaying a fake automatic mode that silently falls back to English.
- The model-switch UI regression passed for Chatterbox, XTTS, F5, CosyVoice, Kokoro and Spark.
  It hides unsupported auto choices, shows inferred language as a readout, and displays the
  actual preset/design/clone source in the scene list. QA restart preserved exact project/job JSON;
  explicit auto requests for Chatterbox/XTTS were rejected before queueing. No user project was used.
- Seven missing Qwen-ASR language names now map from ISO tags to native English names.
  This closes request formatting gaps; actual speech quality across all30 languages is still unverified.
- The sequential root/fresh repeat of all33 previously passing variants completed with zero
  failures after shared adapter/language changes. Reports retain current source fingerprints,
  readiness and artifact-change checks. Prior reports remain preserved as
  `inference-before-language-regression.json`. Further downloads continue independently.
- Updated root and fresh native inspection each covered3,053 objects in12 environments:
  no external absolute dependencies, escaped interpreters or declared minimum OS above14.
  All13 root and fresh dynamic import probes passed;416 external RPATH search entries
  remain a separate static qualification. This is not a Windows/Linux/platform certification.
- MOSS SoundEffect completed actual installation and root/fresh generation. Its codec produced
  3.12s for a3s request. Generated effects now trim/pad to the requested sample count with a5ms
  tail fade; both root/fresh repeats produced exactly3.0s. The verifier now checks this contract.
- The workbench generated and played OpenVoice conversion, then exposed a browser download
  naming defect: the API's inline UUID filename overrode the UI's intended filename. It now
  serves inline without forcing a name; the regression has35 passing Java tests. The new JAR
  runs only on the separate7084 QA root. Exact project/job JSON survived its restart, and
  real OpenVoice/MOSS browser downloads passed with the exact intended filenames and bytes
  matching their server WAVs. Seeking/playback also passed; the MOSS UI returned exactly3s.
  Production JAR remains untouched.
- Dots MF also completed root/fresh generation (19.91s/18.41s). Its transcript and full UI
  checks are pending; it is included in the expanded compiled-UI batch.
- Parler Mini completed root/fresh synthesis (37.5s/34.14s), as did Dia1.6B
  (22.55s/19.77s). These are valid short audio and artifact-readiness checks; their
  short English phrases subsequently matched the local Whisper Large V3 screen exactly.
  Their compiled-UI acceptance remains a separate pending check.
- IndexTTS2 completed actual pinned installation and root/fresh short English cloning
  (85.94s/76.12s); output WAVs were non-silent and pinned artifacts remained unchanged.
  Root and actual compiled-UI recordings subsequently matched their short English phrases
  exactly in local Whisper Large V3 screening.
- LongCat completed pinned installation and root/fresh short synthesis (11.07s/10.68s),
  with valid audio and unchanged pinned artifacts. Root and compiled-UI short phrases both
  matched the local Whisper Large V3 screen exactly. The expanded synthesis UI count is27;
  source/build fingerprints are recorded separately for the later batches.
- Higgs Audio completed pinned installation and root/fresh short synthesis (7.41s/7.99s).
  Its actual UI generation and short/UI phrase screens passed; long synthesis/pause passed
  (23.77s), with a.9947 transcript disagreement retained for independent review.
- The wider UI regression exposed a real scene-navigation defect: adding/duplicating/undoing
  a selected scene changed React state without updating the URL. Reload then opened an older
  scene even though all draft text/audio remained saved. Selection now synchronizes valid scene
  IDs to the URL and resolves deep links after project loading. Five focused state tests passed;
  real creation of three distinct scenes, individual reloads, tab navigation and a non-first deep
  link passed. Earlier UI reload claims were withdrawn and all affected model UI cases were rerun
  with exact scene ID/title assertions; prior reports are retained separately. All23 installed
  synthesis variants passed actual compiled-UI generation, explicit new-take selection,
  immutable submitted text, preservation of concurrent draft edits, paused seeking/playback,
  WAV HTTP206 ranges and exact scene reload. The report records source/build hashes.
- MIT was selected by the user. Python wheel and source distribution built offline using
  pinned Hatchling1.33.0; wheel metadata contains MIT and both license/notice files. Actual archive
  inspection found no runtime caches, virtual environments, profiles, generated outputs or
  node_modules. This is build/packaging evidence, not approval of every model or release.
- Original Inter, React, React DOM, Scheduler, Phosphor and Vite notices now ship in the
  compiled frontend. All six files were retrieved through the Java HTTP server and matched
  their source SHA256 exactly. Third-party source/wheel/model labels are indexed in
  `THIRD_PARTY_NOTICES.md`. The user selected MIT for the application code. The root license, Python/Java/frontend
  metadata and compiled frontend copy now record MIT; third-party terms remain separate.
- A new isolated compiled UI/API on7084 completed all23 installed synthesis variants.
  Its first Fish job generated, sought/played and preserved edited draft text; the harness
  initially asserted the catalog label before its async reload finished. It now waits for
  that actual model load, distinguishes model names/formats exactly and explicitly selects
  the new take when a previous manual take selection is retained. These harness corrections
  are separate from the real scene URL defect described above.
- Local Whisper Large V3 screening recovered the complete intended short phrases for all23
  compiled-UI recordings, including Dots MF. This does not certify subjective voice quality,
  emotion, every language, or long recordings. All9 installed ASR variants also completed
  actual catalog selection, file upload, frozen model request, waveform seeking, transcript
  review/correction and durable voice-profile save through the isolated compiled UI.
  The nine prepared reference WAVs had identical SHA256 for the same source/excerpt;
  raw transcripts are retained separately from the explicitly corrected profile text.
- The expanded compiled-UI run reached26 synthesis variants with no technical workflow errors.
  IndexTTS2 matched its full phrase, while Parler Mini omitted part of a different phrase and
  Dia omitted its final word. Independent Qwen-ASR also found those omissions (agreement.5965
  and.9343), so these are retained quality review cases despite successful WAV/playback/reload.
  Both transcript scripts now require exact normalized text to mark a recording screened;
  every mismatch is review, including cached reports. The previous.85 threshold could miss a
  lost ending and no longer classifies such cases as screened.
  Parler's more detailed supported English voice description retained both sentences but
  mispronounced “interface” with both tested seeds (ASR agreement.9306/.9241). Dia's alternate
  seed7 matched the complete phrase, while seed42 again lost its ending (.9104). These
  model-dependent quality cases remain open; retrying is not a guarantee for arbitrary text.
- A real Resemble denoising run used anonymous generated Russian speech mixed with generated
  rain at0dB input SNR, plus noise-only margins. With100% noise removal and0% restoration,
  noise-only RMS dropped42.40dB and all319,624 frames at44.1kHz were retained. This is a
  controlled synthetic mixture, not a street-recording guarantee. Whisper agreement dropped
  from1.0 before to.8874 after; independent Qwen-ASR dropped from.975 to.6803. Default30%
  restoration and softer70%/50% noise settings did not remove Whisper's word disagreements.
  Noise suppression is confirmed, but natural speech fidelity in this case is NOT passed.
- Actual OpenVoice and MOSS SoundEffect result panels were captured in RU/dark and EN/light
  at320,390,768,1280,1366 and1920px (24 frames). Visual inspection caught the effect-description
  textarea squeezed into the form's auto-width grid column. Shared form textarea now spans
  the full row; the isolated frontend was rebuilt and the24-frame test repeated with a
  full-row-width assertion, playback and exact browser-download checks. Production frontend
  build/JAR were not replaced. Hallmark static lint:0 FAIL, two existing answered warnings;
  its render tier was unavailable, while actual screenshots came from Playwright.
  A separate fresh-context Hallmark finish reviewer inspected the changed source and four
  actual desktop/phone screenshots, returned ship and found no actionable regressions.
- Silero's latest direct-download retry failed after60.9s in TLS handshake with the author's
  server. Official model/version metadata remains confirmed; availability is not proved.
- A new official-host HEAD probe also timed out in SSL connection (10s); the author's
  current models.yml still lists the same v5_6_ru.pt URL. No unofficial replacement or older
  model was substituted, and this remains a download/inference gate.
- A queue-capacity regression reproduced a real cancellation defect: a cancelled pending job
  stayed in the executor's bounded queue, so immediate replacement received429 while the
  active task was still running. Pending tasks now retain their own runnable handle and
  cancellation removes that exact queued runnable. The new test verifies full-queue rejection,
  immediate replacement, no execution of the cancelled task and successful following jobs.
  Before-fix test failed as expected; all36 Java tests pass after the fix. The first full-suite
  attempt lacked sandbox permission for local sockets/process inspection; the authorized
  rerun passed and built a separate immutable queue-capacity-server JAR. The idle isolated7084
  API now runs that JAR. Exact project JSON,44 jobs and11 voice profiles survived its restart;
  the user's production JAR was not changed.
- The new opt-in `verify-model-scenarios.py` tests installed synthesis variants on681/715
  characters, automatic400-character splitting, three generated parts and an explicit1.25s
  PCM-zero pause. It keeps exclusions explicit, checks immutable model artifacts and records
  expected speech separately from application pause markup for later transcript review.
  All27 selected variants completed real three-part audio and PCM-pause checks. Whisper Large V3
  recovered11 long phrases exactly;16 require review. Several Russian differences are е/ё
  orthography, while others include different words or omissions (CosyVoice, FireRed, XTTS,
  Parler and Dia among them). Raw word differences are retained; no blanket quality pass is
  inferred from high character similarity. Fresh-runtime long repeats remain pending.
- Release inspection found local legacy WAVs copied verbatim from `frontend/public/audio`
  into the web artifact. Vite no longer copies the public directory wholesale; packaging
  explicitly ships license notices and refuses an audio directory in the client build.
  Actual isolated build contained no audio/media files; original local WAV hashes were unchanged
  and57 frontend tests passed, including the two packaging privacy regressions. Java now serves
  only the three known local sample names from private `data/studio/samples` or the legacy
  source path, and montage/cleanup share that resolver. All37 Java tests passed. The isolated7084
  API now runs the separate immutable private-assets-server JAR; exact project/job/profile JSON
  survived restart. Its old compiled-only fixtures were retained in local sample storage,
  then all three actual WAV responses/ranges and browser seeking/playback passed. An initial
  browser harness assumed row order matched sample numbers; it now reads each row's real URL.
  No local user recording was deleted, replaced or included in the new web build. Production
  server/frontend remain untouched.
- Dia review found an actual context-format mismatch with the author's cloning guidelines:
  reference transcripts lacked speaker tags, the public wrapper split dialogue turns again,
  and the generic2048-token budget was below the checkpoint's native3072 generation budget.
  The adapter now labels cloning context, joins a continuing speaker turn, appends the native
  alternate-speaker end marker and uses one native generation call with its configured length.
  Four prompt-contract tests passed (71 total Python); root/fresh short inference passed
  (12.36s/11.67s), followed by the long three-part/pause case (72.24s). Both root short and
  long recordings matched the complete intended text in Whisper Large V3 screening.
  Compiled UI also passed and retained its complete phrase. Alternate seed/dialogue and fresh
  long repeats remain pending. Earlier reports
  remain as `inference-before-dia-context-fix.json`.
  Other adapters are unchanged, but the final complete-model repeat still remains required.
- VibeVoice1.5B initially failed strict alignment because the native loader did not account
  for its declared tied word embeddings. The adapter now aliases the existing input embedding
  tensors into the output head only when the checkpoint explicitly declares tying; strict key
  and shape checks remain enabled. No random head was introduced and no pinned file was edited.
  Generation then exposed float32 speech features entering a bfloat16 language KV cache.
  Language inputs now use the actual embedding-output dtype while diffusion retains its own
  numeric behavior. Five weight-contract tests passed (76 total Python), root/fresh short runs
  passed (9.74s/9.22s), and real UI generation/reload/playback passed. Short, UI and long phrases
  matched Whisper Large V3 exactly; the three-part long/pause run took60.29s. Both initial
  failures remain in separate before-fix reports. The wider synthesis UI count is now29.
- Updated long coverage:29 variants completed technical audio/pause checks;13 current long
  recordings match exact normalized text and16 still require review. Dia's lost ending is
  resolved by the context fix. ASR orthography is not silently normalized into a quality pass.
- The independent installation was updated from its old source through the documented
  bootstrap, after all three idle QA servers using its runtimes were stopped. Old code/builds
  were backed up; data, outputs, model caches and its own node_modules remained local.
  The upgraded Python package points to its own source with MIT metadata;37 Java tests,
  eight HTTP-served notice files, source fingerprints and private-audio exclusion were verified.
  Its three prior projects and one old job survived; the new optional request voiceMode appeared
  as null without changing existing values. The catalog QA root retained four projects,47 jobs
  and11 profiles; all29 generated WAV hashes and nine prepared-reference hashes still matched.
  Actual fresh UI Piper Denis generation, immutable submitted text, concurrent draft edits,
  exact scene reload, HTTP206 audio and all six views passed. The fresh cache still contains
  only the previously installed Denis weights; no different Piper was silently downloaded.
  Missing optional legacy sample HEADs returned404 on the empty sample source and stayed hidden.
  All13 post-upgrade offline native import probes passed with zero external loaded libraries.
- Optional macOS resource collection now records `/usr/bin/time -l` maximum resident set size
  for real job processes and waited-for descendants. This is not a simultaneous process sum
  or total system/Java/browser memory. A128MiB-child calibration confirmed descendant accounting;
  a real Piper Dmitri repeat passed and reported223,690,752 bytes maximum RSS. The final
  per-model resource sweep remains pending; file size is not substituted for memory usage.
- Independent Qwen-ASR review recovered the complete long Higgs phrase and the Chinese
  zf_xiaoni/Japanese jm_kumo Kokoro phrases exactly. It also recovered FireRed's ending that
  Whisper missed (remaining differences е/ё). These disagreements do not prove bad model
  speech. Qwen also recovered the corrected Dia UI phrase exactly. CosyVoice's missing
  predicate was confirmed by both recognizers; XTTS and Eric still require closer review.
- Large VibeVoice initially followed the generic SDK loader because it carries its own
  tokenizer, bypassing the input-dtype fix used for1.5B. Both variants now use the strict
  local loader and an appropriate local tokenizer. Root/fresh large-model runs passed
  (7.01s/7.19s), with maximum OS RSS9,804,578,816/10,145,726,464 bytes. These are short-job
  process metrics, not a minimum-RAM promise or total app memory. Root/UI/long phrases all
  matched Whisper exactly; the long three-part/pause run passed in40.42s. The full synthesis
  UI count is30. Before-fix alignment/cache/loader failures remain in separate reports.
- The official CosyVoice3 example includes an assistant/end-of-prompt boundary before the
  reference transcript; the pinned MLX zero-shot wrapper encodes ref_text verbatim. The
  adapter now adds that boundary without editing the stored profile, preserves an existing
  native marker and does not trigger implicit Whisper. The SDK-boundary regression passed
  (77 Python tests), root/fresh short repeats passed (8.31s/6.99s), and the long/pause case
  passed (14.15s). Its previously missing predicate was restored; Whisper now differs only
  on всё/все and завершён/завершен (.9964). Actual UI generation and its full phrase also passed.
- Current long coverage is30 technical passes,14 exact Whisper screens and16 review cases.
  Independent screens above resolve some recognizer disagreements, not perceptual certification.
- Remaining functional audits include expanding voice-import language choices beyond the
  current RU/EN/auto restriction to match the selected ASR's declared languages, proper native
  Japanese input handling where required (CosyVoice3's author requests katakana), and the
  advertised emotion/streaming capabilities versus the controls actually connected to the UI.
  These are tracked gaps, not assumed complete. No model or Japanese coverage was removed.
- OpenAudio S1 Mini remains pending legitimate author access; the user has no local weight folder.
  No access gate was bypassed. Production readiness remains unapproved for all46 entries.

## Evidence gathered so far (chronological)


- All406 pinned file records were compared against author manifests. All HF records match;
  Silero direct server timed out, so its availability remains unverified. No gate bypassed.
-13 isolated runtimes passed offline import probes;13 initially installed models
  completed real short technical tasks. This does not establish all presets/languages/quality.
- Current checks:57 Python tests,47 frontend tests and32 isolated Java tests passed.
  Counts are evidence for the covered contracts, not all model behavior.
- Real UI: project creation, Piper selection/generation, immutable submitted text, waveform
  seeking/playback, reload persistence, second scene, project search/export and library search passed
  against a separate API/database. All six initial views loaded without JS/HTTP errors.
- Fixed Piper's native phonetic-data path failure in deeply nested project directories;
  all four Piper voices subsequently generated valid output.
- Fixed cross-checkout Python imports in Java generation/catalog/assembly subprocesses.
  A shared editable venv previously wrote a QA result under its original checkout. The bridge
  now explicitly imports code from the configured project; the same UI scenario passed.
  The single generated QA artifact was moved to its intended isolated folder. User projects,
  metadata and existing recordings were not altered.
- Closed hashed file streams during model import/archive checks; ResourceWarning-as-error
  run of the39 Python tests passed.
- Additional actual downloads are running serially; complete installation, cancel/resume and
  real inference on the remaining variants are still required.
- Production Java process remains on its prior jar. New Java changes are built/tested in a
  separate jar; rollout must happen after the release verification, without overwriting a live jar.
- Current isolated Java test count:32, failures/errors:0.

- Voice UI: upload/ASR, manual transcript correction and atomic save, Qwen cloning from the new
  profile, preservation of edits made during a running job, cancel/confirm deletion, and preservation
  of both generated audio and scene draft after profile deletion passed with isolated real services.
- Standalone enhancement UI: actual denoise/restore, matched Before/After seeking, dirty-setting
  download guard, discard, cached new version at0% restoration, original version preservation,
  download and reload passed. Scene/master application and cancellation still need current regression.
- Local ASR screening recovered the intended short phrases from all11 generated/processed outputs;
  minor recognizer differences remain. This screens gross failures, not subjective similarity/quality.

- Microphone regression: Chromium fake input (physical microphone unused), explicit permission
  request, real meter, pause/resume timing, finish/release, cancel preserving old file, navigation
  cleanup, denied/late permissions and AudioContext cleanup passed;12 responsive captures.
- Optional Xet transport completed one463.66MB Whisper Turbo weight download in1638.8s
  on this connection. Standard installer is also making byte progress; no speed guarantee inferred.

- Whisper Turbo completed actual download, studio installation/selection and real Russian ASR.
  Technical model smoke coverage is now14/46. Model UI cancel/restart flow passed on
  Whisper Medium; it remained unready after cancellation. No model was made ready from
  a partial download. All model selection changes in these UI tests used the QA data root.
- The first download verification runner stopped Qwen1.7B after its own40-minute test limit
  while bytes were still arriving. This is a test-harness timeout, not evidence that the
  production installer is broken. Partial files were retained. The harness now checks idle
  progress (10 minutes) with a24-hour absolute limit and prioritizes smaller artifacts.
  First-run logs are preserved as `downloads.json.run1` and `download-progress.log.run1`.


- GigaAM v3 now performs real Russian ASR without importing its unused optional, gated VAD
  dependency. Whisper Medium and Chatterbox Turbo also completed actual short inference.
  Technical coverage is18 distinct variants; previous cases need reruns against the final source
  fingerprint. Successful output is not subjective quality or complete language coverage.
- Kokoro's54 catalog presets all produced valid audio after adding the missing full UniDic3.1
  dictionary as a hash-pinned local bundle. Extraction stays inside the project, retains licenses,
  checks disk expansion and rejects corrupt/unsafe archives. All 54 presets were rerun. Offline
  Whisper Turbo screening matched the test phrase closely for53 presets; zf_xiaoni needs manual
  Mandarin review (character agreement .5333, partly homophones). ASR is not a perceptual verdict.
- Montage real UI regression passed: pointer/keyboard ordering, undo, exclusion, .3-2.1s trim,
  −6dB scene gain,5s per-scene gap,1.25s default gap, reload and actual WAV/MP3 export.
  The rendered12.05s WAV had the expected duration and exact digital silence in both gaps.
- ASR language compatibility is checked before processing. Voice imports now freeze the
  selected model before entering the queue and preserve it through restart/save. Real compiled
  UI verification queued an English sample behind enhancement, switched the current model
  to Russian-only GigaAM, and still received the correct Whisper Turbo English transcript.
- Full setup completed in a fresh folder containing spaces, with independent caches and no
  pre-existing model weights, venv or frontend dependencies. Official pinned archives were
  hash checked; Java/Node/Maven/Python are local. A PyTorch transfer timeout and pnpm11's
  explicit esbuild build permission initially stopped setup; both were fixed and the resumed
  setup/build and31 Java tests passed. Browser startup and the first fresh model installation/generation also passed.
  The initial QA fixture's toolchains alias into the Python folder was separated before the final
  successful setup; that fixture error is not a product dependency.
- Java now serves the compiled frontend and API together. Real HTTP tests verify root/query
  routes, assets, MIME/cache headers, private-file/traversal rejection and missing-build handling.
  QA browser flows run without Vite. The documented live-JAR overwrite guard was exercised:
  it refused the build and the running production JAR's SHA256 stayed unchanged.
- Catalog density verification passed24 RU/dark and EN/light viewport combinations from320
  to1920px:1/2/3/4 columns,46 intact cards, no horizontal overflow or JS errors. Search, empty
  state, task filters, source disclosures and clamped dropdowns were checked at representative
  desktop/mobile widths. Existing user projects were isolated from all browser mutations.
- Installer verification is still live. Several later model attempts failed during DNS/transport
  outages; the logs distinguish network failures from inference failures. Retained partials need
  retries. OpenAudio author-gated weights still require legitimately obtained access/import; the user
  confirmed that no downloaded folder is available.


- Fresh browser flow without models: all six tabs opened, missing-model generation guard worked,
  Piper Denis installed its own weights/runtime from the UI, generated a real take and retained
  exact text/audio after reload. No shared model or dependency cache was seeded into that install.
- Real two-browser-context conflict flow passed: offline edits survived reload, retry detected a
  concurrent server text edit, Save my copy preserved both projects, and Load server version
  retained a recovery backup of the local draft. No user projects were used.
- Real scene/final enhancement passed: explicit scene application retained the original file hash,
  draft text, original take and trim/gain settings; reopening selected the existing enhancement.
  Enhanced master stayed separate, downloadable and reloadable, with scenes unchanged.
- Actual cancellation exposed a Java/Python lifecycle race: after cancelling enhancement,
  the following Piper request failed with Stream Closed. PythonWorker now invalidates the old
  process under a lifecycle lock before another exchange, including errors/deadlines. A real
  subprocess regression and32 Java tests passed; the fixed QA server passed running/queued
  cleanup cancellation, a following Piper job, retry and cancelled-version preservation.
- Master enhancement resampling originally left29 nonzero edge samples in a1.5s inserted gap;
  neural restoration amplified those samples. Canonical conversion now restores source PCM
  silence ranges before inference. The repeated real5.5s enhanced master contains zero nonzero
  samples across the entire2.0-3.5s gap; source audio and duration remain unchanged.
- Spark-TTS completed an actual2.21GB installation. Its first inference exposed a BatchNorm training-mode error in the
  audio tokenizer. The adapter now switches the plain tokenizer container’s neural modules to
  inference mode. Actual generation passed after this fix; local Whisper Turbo recovered the
  exact test phrase apart from punctuation. All17 previously installed variants passed the
  preceding repeat regression; the new Spark fix affects only the Spark branch.


- Fresh setup was repeated against updated source and restarted with its existing database,
  takes and model cache. Project JSON, completed-job metadata and selected Piper model matched
  their pre-restart values exactly. Actual audio HTTP206 ranges, HEAD length and invalid416
  ranges passed. No running JAR was overwritten during the upgrade.
- Browser legacy migration passed in two independent contexts: the same old draft created one
  server project, retained code/numbers/URL literals and its old localStorage backup. Repeating
  the migration did not overwrite a subsequent server text edit or create another project.
- Real Fish idle measurement passed at180.33s. MLX active allocations fell from6,579,161,668
  bytes to28 bytes and allocator cache to0; observed peak MLX allocation was10,627,738,567
  bytes for this short sample. These counters are not total system memory or a guarantee for
  longer text/other hardware. RSS was measured separately and must not be presented as GPU RAM.
- The user confirmed no OpenAudio S1 Mini folder is available. Actual licensed weight import
  and inference for that entry remain pending author access. Other model verification continues.
- DNS-failed Whisper Large V3/Qwen3-ASR downloads are being retried in a separate report/log
  directory; this disjoint weight batch shares the local cache but cannot overwrite the main
  verifier report. Inference remains serial in the model verifier.


- Actual montage WAV/MP3 export parity passed: both decoded to578,400 frames at48kHz;
  waveform correlation was0.999981. MP3 is lossy and was not claimed byte-identical to WAV.
- Optional Python3.11 is now pinned to3.11.18 and uv must use a managed interpreter inside
  the project; an installed system interpreter cannot satisfy that path. Setup timeouts allow
  the managed-Python download and large wheels. The isolation regression raises the Python
  suite to53 passing tests. A separate fresh-runtime installation/probe batch is now running
  against the independent fresh-install dependency cache; native external-library inspection
  and inference from these fresh optional runtimes remain required.

Latest model coverage:20 distinct variants completed short real tasks. Whisper Large V3
passed Russian ASR after retrying its failed transfer; VoxCPM2 installed and generated
audio in12.35s. This is technical smoke coverage, not a quality or full-feature verdict.

Fresh-runtime findings and repairs:

- Kokoro's Japanese dependencies had no suitable upstream Python3.13 wheels. The project
  now includes hash-pinned local wheels, exact upstream source archives and license notices.
  Their binary-only installation passed with the compiler disabled. All five Japanese
  presets generated audio again using the independent fresh runtime from a folder with spaces.
  Model weights were shared for that inference check; it is not a fresh weight-download claim.
- CosyVoice's VAD failed to import because upstream used the removed `pkg_resources` module.
  A retained metadata-only compatibility patch and local CPython3.11 wheel fixed the import.
  Binary-only installation and a real silence-frame VAD check passed without `pkg_resources`.
- Static inspection covered2,941 Mach-O files in12 physical environments: no absolute
  loaded-library path or interpreter escaped the project/system, and no binary declared a
  minimum OS above14. Some unused external RPATH search entries remain; static load commands
  do not prove all possible dynamic loading paths. Offline dynamic probes separately cover
  libraries actually loaded during imports. Hardware/OS variations still require real tests.
- All 57 Python tests passed after these bundle changes. All 11 optional environments completed
  installation and offline probes with the independent fresh dependency cache. Together with
  the two base aliases, all13 fresh dynamic probes passed with no external loaded libraries.
  Static inspection of that fresh installation also covered2,941 native objects with zero
  external absolute library dependencies, escaped interpreters or declared minimum OS above14.
  The same413 external RPATH search entries remain a separate qualification.
- The first deeply nested fresh Kokoro inference exposed eSpeak's native data-path limit:
  the process exited while looking for its build-machine dictionary path. Pipeline construction
  now shortens only the checked native path argument, with the override restored afterwards.
  A regression covers spaces/deep paths and restoration on exceptions. All 20 installed variants
  then completed real tasks using independently installed fresh runtimes. Model weights were
  reused from the verified shared cache. All 54 Kokoro presets also completed the fresh repeat.
- All 13 updated offline dynamic runtime probes passed with no loaded libraries outside the
  project/system. CosyVoice's fresh first import exceeded the former60s cold-cache limit;
  setup now allows180s. The patched VAD subsequently passed binary-only installation and its
  real silence-frame probe in the independent fresh runtime too.
- Separate cold-bytecode-cache probes passed for fresh Torch (25.46s) and CosyVoice (10.59s),
  with compiler commands disabled and network offline. A source-archive timeout initially
  interrupted the fresh legacy adapter installation. Source fetching now retries transient
  transfer errors up to three times with a300s socket limit; hashes must pass before extraction.
  Interrupted-transfer and corrupt-archive regressions passed, and the real fresh retry completed.
- VoxCPM2 passed the compiled UI flow: model selection, generation, seeking/playback, reload,
  project JSON export and library lookup without JS errors. Local Whisper Large V3 screening
  matched the expected text for all14 generated/processed short cases. All 54 fresh Kokoro presets
  were screened too:53 matched closely; zf_xiaoni still needs Mandarin listening review
  (character agreement .3333 on this repeat). Recognizer disagreement alone is not a quality verdict.
- Catalog capability flags still need reconciliation against actual exposed controls. For
  example dialogue flags do not establish multi-speaker profile controls. VoxCPM2, OmniVoice
  and Spark voice modes were subsequently connected and verified (see current checkpoint).
  Do not present those flags as tested app workflows before that gap is resolved.

## Next required work (goal remains active)

1. The public download verifiers have completed. Resolve the official Silero TLS failure and
   verify legitimate OpenAudio S1 Mini weights when available; never bypass author access gates.
   For any new transfer, retain/resume partials and verify files; do not restart on observation timeout.
2. Run actual inference on each newly installed variant and fix adapter/bundle/runtime failures.
   Extend tests to applicable presets, languages, markup, long text and repeat runs.
   Check each advertised capability against actual controls, including dialogue;
   family feature flags alone do not prove the corresponding UI workflow.
3. Preserve the successful isolated UI, montage/export, enhancement, cancellation/queue,
   conflict/offline/restart/migration and audio-range evidence. Extend coverage to newly installed
   model-specific controls, languages and errors; repeat other flows only when affected by a change.
4. Complete fresh-install UI/model inference and launcher restart/relocation checks. Full bootstrap
   now installs locked project-local Java/Node/Maven/Python/frontend prerequisites; empty-cache
   compilation passed after fixing the network timeout and esbuild build allowlist.
5. Profile resources, verify platform declarations, dependency/license/access restrictions,
   anonymous release assets and all release gates. Roll out the Java jar only after validation.
6. Do not certify all46 models or production readiness from the currently successful subset.

## Reference language validation and UI: 2026-10-31

Removed the RU/EN-only reference-language restriction across Java, Python and the voice form.
The form now exposes languages declared by the selected recognizer; it retains an unsupported
draft selection and blocks submission with an explanation instead of silently changing it.
A health capability keeps the updated client compatible with older servers. Recording language
is independent of interface locale. Existing profile schemas and files stay unchanged.

Evidence: `reference-languages/ui.json` and three real browser screenshots in the ignored audit
directory: Qwen3-ASR explicitly transcribed a Japanese recording, manual review saved the profile
with `language: ja`, and reload retained the exact transcript. Switching to GigaAM preserved the
Japanese draft but disabled submission; switching back restored eligibility. The language menu
remained within the viewport at320/768/1366px with no page horizontal overflow. The anonymous
source was an existing Kokoro Japanese preset output with only trailing digital silence added
to meet the reference minimum length; this is not a real-speaker similarity evaluation.

Latest checks:79 Python tests,59 frontend tests and38 Java tests passed. Java integration tests
needed local loopback/process permissions; the first sandbox-only run is preserved in tool history
and was not counted as passing. The QA7084 API now uses the separate immutable
`voice-languages-server` JAR and compiled UI; old JAR/build and source backup remain available.
The user's production API and preview were not replaced. Full language/model quality audit remains
in progress. MIT was explicitly selected by the user and is present in LICENSE and all three code
package metadata sets; model and dependency licenses remain separate.

MOSS VoiceGenerator is now43rd catalog variant with successful real root/fresh-runtime output.
The first real run failed because the author's custom processor forwards `local_files_only`
into ProcessorMixin, which rejects it. The adapter now resolves the pinned local processor class
first and invokes its native loader without that leaked argument. Nested config, tokenizer and
codec loaders retain the existing local resource guards; model files are unchanged.
Evidence: root/fresh `inference.json` rows; pre-fix report snapshot; unit boundary regression.
Root/fresh short runs took16.41/19.64s, maxRSS11,222,974,464/12,060,917,760bytes. These are process
RSS measurements excluding Java/browser, not minimum system RAM requirements. Root Whisper LargeV3
found exact normalized text; actual UI generation, frozen draft, take selection, range playback
and reload also passed, bringing synthesis UI coverage to31 variants. Long text and additional
quality/capability checks remain pending. Python now80 tests.

Language menu: English/light320/768/1366px, Home/End/typeahead/Enter, and locale switching now
pass (`reference-languages/english.json`). Fixed typeahead retaining its search prefix after
closing/reopening a Select. Shared Hallmark static sweep:0FAIL,2existing WARN (selected-option
fill is a selection state; repeated field surfaces are intentional consistent form controls).
The skill render tier is unavailable without its browser package; actual Playwright screenshots
were captured. No new visual layout or dependency was introduced for this change.

Japanese Chatterbox follow-up: a same-language reference profile now passes the complete UI
path, but Whisper's transcript still differs substantially from the intended Japanese sentence
(character similarity0.4906; raw audio/text retained in `reference-languages`). It remains a
quality issue, not a successful language-quality certification. The SDK's v3 tokenizer explicitly
uses NFKD/fullcase and bypasses legacy Japanese transforms; do not apply v2 hiragana processing
blindly. Both the earlier cross-language-reference test and this same-language test are retained.
The UI MOSS VoiceGenerator test transcript is exact normalized text.

MOSS VoiceGenerator long scenario passed715characters/3parts with the requested1.25s digital
silence preserved (66.56s processing). Whisper's normalized comparison is0.9973, with an
additional “and”; retain quality-review status rather than silently dropping that word. This
brings technical long-scenario coverage to31 synthesis variants. Existing QA jobs were preserved.
The next model, MOSS-TTS, is still downloading under the original single download task.

Chatterbox Japanese diagnostic: the pinned v3 tokenizer emits12 unknown tokens for the kanji
test sentence and0 for its explicitly written kana reading. Both actual UI generations are
retained separately. This isolates a preprocessing/token-coverage problem; no universal legacy
transform or model-file edit has been applied. See `reference-languages/token-diagnostics.json`.

Chatterbox diagnostic result: the manually written kana version was recognized exactly as the
intended Japanese utterance by Whisper LargeV3, whereas the kanji version was not. This confirms
a promising preprocessing repair path; the application still needs an automatic, offline,
license-compatible reading conversion before Japanese kanji input can be called supported.
Do not count the manual-kana diagnostic as a production adapter fix. Both submitted scripts and
outputs are separate immutable UI takes (`japanese-ui.json`, `japanese-kana-ui.json`).

## Automatic Japanese readings: implementation under verification

Added offline Fugashi/UniDic readings for Chatterbox Japanese kanji input and CosyVoice
Japanese text/reference input. Chatterbox uses kana readings while retaining the original
katakana, ASCII, numeric literals, punctuation and whitespace. CosyVoice uses katakana
pronunciations as requested by the author's official example (FunAudioLLM/CosyVoice example.py).
Chinese kanji alone do not trigger automatic Japanese conversion; CosyVoice now permits an
explicit language selection, including Japanese for ambiguous kanji-only text. Source scripts
and stored reference text are never overwritten. Unknown readings and dropped token surfaces
fail explicitly instead of silently discarding content.

UniDic is included as a hash-pinned required resource in both model bundles, with actual
download/unpacked sizes and original notices. Fugashi1.5.2 is the only added CosyVoice
dependency; all pre-existing locked versions are unchanged. Root/fresh runtime install passed,
all13 offline import/dynamic-library probes passed in each environment, no external native
libraries were loaded. Four new reading regressions passed; total84 Python tests passed.
Real dictionary conversion is recorded in `japanese-normalization/readings.json`.
Actual model/UI quality and post-install regression are still pending at this paragraph's checkpoint.
The QA source backup is retained at `catalog-ui/app/src-before-japanese-normalization`; user
production processes remain unreplaced.

Automatic Japanese verification: Chatterbox from original kanji input passed the complete
compiled UI path on the independent runtime, then a separate root-runtime generation.
Whisper LargeV3 recovered the full original sentence exactly in both cases. Source job/project
scripts remained original kanji; source/reference files were not rewritten. The earlier broken
and manually written-kana diagnostics remain separate records. Russian short runs passed again
in root/fresh runtimes (11.4/13.77s).

CosyVoice Japanese original-kanji UI generation, explicit language, immutable draft, playback,
range requests and reload passed. Actual voice/reference preprocessing uses the local dictionary.
Both Whisper and Qwen-ASR detected a small added Japanese prefix in the test utterance, so
quality remains review rather than exact fidelity certification. Russian short repeats passed
in root/fresh runtimes (10.69/26.38s). UI layout was checked at320/900/1280/1366/1920px in
RU/dark and EN/light: no horizontal overflow, draft preserved, desktop language/generation
controls visible;1366 screenshot visually inspected. The first responsive test captured the
empty editor before the project loaded; the harness now waits for the actual project.
Root and independently installed Python suites each passed84tests.

Independent ASR of the long MOSS VoiceGenerator recording disagreed with Whisper's exact
wording at a different small point (Qwen omitted “to”, Whisper inserted “and”). Both raw
transcripts remain in `japanese-normalization/independent/results.json`; disagreement is not
a model-fidelity pass or proof of a particular spoken error. Listening/quality review remains.

## MOSS-TTS strict codec repair and real verification

Original install finished successfully under the same download process;44variants are now
installed. Initial real inference exposed two issues not found by import probes: the pinned codec
uses the `mlx-int8` subdirectory, and the native SDK codec loader ignores INT8 configuration.
It also renames only `.weight` keys while leaving scales/biases under the old transformer names,
and expects weight-normalization parameters where the export contains fused Conv1d kernels.

The adapter now records/passes the codec subdirectory and preloads a project-owned strict codec
loader. Weight/scales/biases are renamed together; fused kernels are represented equivalently
by weight-normalization parameters, including finite zero rows. The declared8bit/group64
quantization is applied only to modules with checkpoint scales; strict key/shape validation is
retained. No missing tensor is ignored, no random output substitute is used, and no model file
is rewritten. Four regressions cover native codec injection, aligned quantization metadata,
convolution equivalence/zero rows and duplicate-key rejection. The first unit fixture lacked
its mandatory model repo field; the corrected test and full suites passed.

Root/fresh real short synthesis passed17.91/17.21s; resulting speech8.48/6.00s. Measured maximum
RSS7,198,818,304/10,219,913,216bytes excludes Java/browser and does not establish minimum RAM.
The compiled UI generation/frozen draft/selection/playback/range/reload path also passed,
bringing synthesis UI coverage to32variants. Root and independent Python suites each passed88
tests. Long text and transcript review are running; do not count those as complete yet.

MOSS-TTS long scenario completed in49.03s with681characters,3parts and the requested digital
pause. Root short Whisper screen is exact; long screen0.9982 remains review under the strict
rule (raw differences inspected). Full technical long-scenario coverage is now32synthesis
variants. The successful UI record additionally carries Java/frontend/Python artifact hashes.
A fresh bounded HTTPS HEAD of the official Silero file again ended in SSL connection timeout
(exit28,25s maximum); no substitute mirror, gate bypass or fake install was used. OpenAudio
S1 Mini still requires legitimate author-gated weights; the user has no local folder.
These two positive-inference gates remain unresolved; the overall release audit stays active.

Evidence indexing correction: the original42 fresh-runtime cases live in
`fresh runtime inference/inference.json`; the latest MOSS additions and two Japanese-adapter
regressions live in `fresh-inference/inference.json` (4rows). They are not two44-row reports.
The union contains44distinct successful variants using the same independent runtime root;
`fresh-distinct-evidence.json` links each original record and all referenced audio SHA256 values
were rechecked. These historical runs do not prove that every variant was rerun on one final
source fingerprint. MOSS-TTS UI Whisper screen also recovered its submitted text exactly.

## Reference duration boundaries: running

Added opt-in `scripts/verify-reference-boundaries.py`: serial real cloning for every ready
clone-capable model at5and30seconds, with per-case model artifact/state checks, immutable
reference/profile SHA256 checks and optional measured process RSS. Inputs are anonymous
synthetic utterances; only complete utterances are appended, with exact matching transcripts
and trailing digital silence to reach the boundary. No speech is cut while retaining longer text.
This is a reference-duration/contract check, not a real-person similarity certificate.

The original snapshot is running22models/44cases. It already found Chatterbox Turbo's strict
`>5s` native assertion conflicting with the app's accepted `>=5s` reference. The adapter now
adds one silent sample in memory for exactly5seconds; original speech, files and transcript
remain untouched. Longer references retain their native path; shorter legacy references return
a specific minimum-duration error. Two boundary regressions passed and the90-test Python suite
passed. Actual Turbo repeat and complete matrix/transcript checks remain pending here.
Separate real UI5s and30s voice-import/ASR harnesses are prepared but not yet executed.

Boundary snapshot completed:41/44cases initially passed; failures were Turbo's exact5s
assertion, Dia30s returning EOS before speech, and Spark30s returning no semantic codes.
Turbo's corrected5s/30s repeats passed6.25/6.33s, and actual UI5s upload→Qwen-ASR→review/save→
Turbo generation/playback/reload passed too. Reference waveform hashes remained unchanged.
Spark now uses its native speaker-code-only cloning path (optional ref_text=None), retaining
the complete source reference and target text. Both5s/30s actual repeats passed7.16/5.58s.
The root model boundary report currently has43passed cases and only Dia30s unresolved.
Source snapshots and failed logs remain available; no failure was hidden or removed.

Dia forced-alignment prototype using the supplied exact transcript succeeded with the local
Whisper BaseQ4 model. It produced word timings, reconstructing every supplied character, and
identified the first complete paragraph ending9.22s in the30s fixture. This is alignment of
original words, not generated replacement text. One prototype call used the wrong spectrogram
axis; corrected axis=-2 matches the installed upstream transcribe implementation. A bounded
reference helper and four pure mapping/selection regressions now exist, but the pinned model
dependency/runtime installation and actual Dia repeat remain pending.

The first30s ASR UI harness waited on `input[max=30]`, which matched the new30s seek slider
instead of the numeric duration field. It timed out before any upload; the selector is now
scoped to the numeric input. This was a test-harness error, not reference data loss.

Completed reference boundary verification:22clone-capable installed models ×5/30s now
produce valid real audio with original profile hashes unchanged. The report contains44passed
cases after scoped fixes. Dia5s/30s repeats passed28.21/25.09s with the declared offline
Whisper BaseQ4 forced-alignment bundle; no stored transcript or source audio was rewritten.
Two explicit short/missing-bundle/oversized-reference regressions bring the Python suites to97
passing tests in both environments. Existing dependency versions were preserved; only
mlx-whisper0.4.3, tiktoken0.14.0 and more-itertools11.2.1 were added to the extended runtime.
Both environments passed all13 offline import/dynamic-library probes, with0external libraries.

Actual UI30s creation passed for all9ASRvariants, including review/correction/save/seek.
All canonical reference waveform SHA256 values match; raw ASR transcripts remain visible
in `catalog-ui/asr-30.json`, including omissions in repeated speech that required manual
correction. This is workflow evidence, not perfect-ASR accuracy. The minimum5s Qwen-ASR→
Turbo UI path also passed; source references were not padded or rewritten on disk.

Whisper screening of44cloned outputs:41exact normalized texts,3substantial review cases:
Qwen0.6B INT4 with30s reference echoed an extra reference phrase; OmniVoice30s mispronounced
part of the target; VibeVoice Large5s repeated the reference wording. Independent Qwen-ASR
review is running before attributing those errors or changing adapters. Native OmniVoice
source inspection also found that its generate() omits ref_text when invoking
create_voice_clone_prompt(), so references>20s can still be cropped at a silence gap despite
the explicit30s maximum. This requires a proper pre-encoded matching reference fix.


The explicit MIT selection is confirmed in LICENSE and Python/frontend/Java metadata;
model and bundled third-party licenses remain separate. All99Python contract tests passed
in both the working and independently bootstrapped runtimes.

Independent Qwen-ASR confirmed all three boundary content errors. OmniVoice now pre-encodes
its complete matching reference/transcript once; its native wrapper had omitted ref_text
and silently cropped >20s audio at a silence boundary. Corrected5s/30s native repeats passed,
and both spoken texts screen exactly with Whisper LargeV3. No source file was modified.

Qwen0.6B Q4 now shares the forced-alignment preparation with Dia: references longer than10s
use a complete-word/sentence excerpt with the matching original transcript. The30s Russian
prototype selected5.8s and produced exactly the target words. The pinned Whisper BaseQ4
bundle is declared in the model download, size and license; core-runtime mlx-whisper0.4.3/
tiktoken0.14.0 and all transitive dependencies are locked. No old dependency version changed;
14packages were added to the core environment (the extended runtime already had most of them).
Root and fresh actual5s/30s repeats passed for Qwen, OmniVoice and Dia. Text screening of
the final repeats is in progress; native success alone is not a fidelity claim.

VibeVoice Large5s still repeats source words, independently confirmed by both ASRs. Removing
only trailing digital silence in an isolated prototype retained the correct target but still
added source words; that speculative preparation was NOT shipped. Catalog notes disclose
this observed limitation; the case is not a release pass. The previous30s/short/UI/long
successes do not establish reliability for every reference.

The first OmniVoice repeat inside the filesystem sandbox could not access Metal and failed
before loading the model; an authorized GPU repeat passed. This environmental failure is
not attributed to the model. The report was updated only by the actual repeat, not by editing
failed status values. Runtime imports/dynamic-library probes were repeated after the lock change.

An isolated QA server log also exposed IOException error serialization retaining audio/wav
Content-Type. Review ApiErrors response content types and add a focused HTTP regression before
release; this is not yet fixed or deployed.


Final checkpoint for this pass: all13offline/dynamic-library probes passed in each environment
with0external native libraries. Qwen5s/30s and Dia5s/30s produced exact normalized target text
in both environments. OmniVoice additionally now derives its duration from the actual encoded
reference and matching transcript through the native estimator, instead of the wrapper's fixed
English placeholder. Corrected30s repeats screen exactly in both environments; fresh5s also
screens exactly. Root5s has an extra-phrase Whisper disagreement, while independent Qwen-ASR
recovers exactly the intended text (audio hash/events preserved). That disagreement stays a
review case; neither ASR is treated as a subjective listening certificate.

A separate compiled UI/API instance on7085 used the independently installed runtimes and
30s reference: Qwen0.6B Q4 and OmniVoice both passed actual generation, frozen requests,
manual draft preservation, explicit take selection,206range, seek/play/pause and reload.
Evidence is in `reference-boundaries-ui/results.json`; user projects/tab4173 were not used.

The audio-header IOException issue is now fixed: API errors set application/json explicitly.
The focused test first reproduced the real converter failure, then passed with the correction;
all39Java tests passed in a NEW immutable JAR build under `error-content-type-server/target`.
The production server/JAR has not been replaced. Root/fresh Python source and tests are synced;
final99-test reruns are recorded in `reference-boundaries/python-final-*.log`.

Still open: VibeVoice Large short-reference source repetition; other previously recorded
quality/preset/cleanup reviews; final stable-source catalog/flow regression and production
rollout; Silero official TLS failure and legitimate author-gated OpenAudio weights. Overall
audit remains active and not release approved.


Additional audit pass: author RMS normalization and post-load seed were tested for both
VibeVoice variants at5/30s, using isolated source copies. VibeVoice1.5B matched both
short/long screens; Large30s matched, but Large5s still copied the source phrase. This
speculative normalization/seed change was not shipped. The short-reference limitation remains.

Corrected cleanup test coverage: the earlier `verify-noisy-cleanup.py` omitted the input's
`cleanup.json` routing marker, so it actually exercised LEGACY restoration, not the studio's
separate denoise/restoration pipeline. Its0dB noise reduction/output hashes remain historical
legacy evidence; its supposed natural-mode and setting-comparison conclusions are withdrawn.
The actual UI cleanup tests were separately routed through the API and are unaffected.

The new public opt-in `scripts/verify-cleanup-scenarios.py` requires that marker, verifies
actual denoising/restoring stages and saved `separate-noise-v2` analysis/options, rejects
ignored settings, checks source/model immutability, frame preservation and cached mastering.
It ran24real outputs: RU/EN ×recorded rain/engine ×0/10/20dB input SNR ×natural/default.
Noise recordings come from the pinned official ESC-50 source in ignored QA only, with hashes,
license and provenance retained; none are shipped. PCM16 measurements cap the noise floor and
mark censored suppression values as lower bounds rather than reporting fictitious198dB.
Whisper and independent Qwen-ASR screened all24outputs,12noisy inputs and2clean baselines.
Both detect examples where restoration changes words. Clean RU synthetic speech already has
ASR ambiguity, so input-versus-clean and output-versus-input records remain separate; none
of those raw disagreements is silently converted into a fidelity pass.

Relocation found two release defects: copied Python environments can retain the original
checkout's managed interpreter while still claiming ready; pnpm prompts for module-directory
replacement and aborts in noninteractive startup. The installer now rebinds relocatable venvs,
repairs already installed optional runtimes, and invokes frozen pnpm installation with a
scoped CI setting. Readiness checks the real environment owner, interpreter and pyvenv home;
explicit QA environment symlinks remain supported. The launcher validates the main environment
before starting. CLI imports are pinned to the current source, and bundled ffmpeg links are
repaired atomically/relatively, including dangling links and /var→/private/var aliases.
The full APFS-cloned relocation bootstrap and later native checks are currently running.

## Verified checkpoint: 2026-11-01

The relocation/bootstrap, full 44-model short sweep in both environments and the
production rollout described above completed. The consolidated current state is in
`release-status.md`; earlier "running"/"pending" paragraphs are historical checkpoints.
Production remains on its immutable tested Java JAR at4173. The old idle QA server7081
was stopped after checking its exact project and empty active queues. User projects
(full SQLite documents/revisions/timestamps), all4protected profile files and77audio
files still match the pre-upgrade records. The initial check comparing the project
summary list with the stored-document map was invalid; the corrected check reads
SQLite in read-only mode and confirms equality.

All32long synthesis scenarios completed and were screened by both Whisper LargeV3
and Qwen3-ASR on identical WAV hashes. Their intersection is11exact,4orthography-only
е/ё,4with one exact recognizer and13remaining lexical reviews. No such review was
silently turned into a quality pass. `model-quality.md` records the scope and cases.

XTTS emitted its native182-character Russian warning on the earlier long test.
The adapter now uses Coqui's per-language sentence splitter before decoding and
reserves one character for the joining space the native splitter omits from its
length calculation (reproduced on Chinese). Merely enabling native splitting first
failed due to absent spaCy. The new actual-language regression also found missing
Pypinyin. Both failures remain in local logs; dependencies now include spaCy[ja],
coqui-tts[ja], Pypinyin and explicit Click (new Typer no longer declares Click while
this spaCy still imports it). All96existing package versions are unchanged;34added
packages are hash locked. Installation/import probes passed in root and relocated
environments, and both dependency checks and13dynamic-library probes passed again
with zero foreign native libraries. The106-test Python suite passes, including
actual splitting/preprocessing of short/long inputs for all17catalog XTTS languages.

The final XTTS real matrix contains8cases: short root/relocated,5/30sreferences,
long Russian with pause, English/Japanese/Chinese with English reference. Both ASRs
are exact on6cases. The5sreference has a one-recognizer lexical mismatch; the long
case retains morphological differences but no longer repeats the earlier fragment
or exceeds native limits. All cases preserve pinned artifacts. All4available models
in the updated Torch runtime repeated real tasks successfully in both environments.
Post-change XTTS RSS is4.09/4.10GiB, and measured output hashes equal the reviewed
short WAVs. This does not prove subjective quality or RAM requirements on other hosts.

Silero's official TLS endpoint still times out on01.11. OpenAudio still requires
legitimate author-granted weights. Other recorded quality/preset/cleanup reviews
remain open; this checkpoint does not approve the full46-model production release.

## Preset review and catalog language controls: 2026-11-01

The catalog exposes80preset choices:75available (Kokoro54, Qwen CustomVoice9,
Orpheus8, four single-voice Piper models) and5Silero choices awaiting its official
download. All75available choices have actual synthesis evidence, from the dedicated
preset matrices and full catalog singleton cases. The eight disputed earlier WAVs
were checked with independent Qwen3-ASR without regenerating them. Seven are exact:
both `zf_xiaoni` outputs, four Hindi voices and `jm_kumo`. `Eric` remains lexical
review. Current WAV SHA256 values equal both the generation records and new ASR
records. `preset-independent-summary.json` retains this distinction. The preset ASR
verifier now runs any installed recognizer in its pinned runtime, checks audio stays
inside the audit directory, and keeps recognizer-specific output files; old reports
are preserved. This does not certify perceptual quality or resolve the other gates.

The model language filter had a real UI defect: only Russian/English were selectable,
and a Japanese URL silently reset to all languages. It now derives choices from the
full catalog. Canonical BCP47 aliases match across models (`ar`/`ara`/`arb`, `ja`/`jpn`),
without changing native model codes or generation requests. The654declared codes
produce644canonical choices. Distinct codes with coincident localized names remain
separate and show their code; metadata is not silently merged by label alone.

The compiled browser test first reproduced a second defect: the selected Japanese
option was thousands of pixels outside the visible long menu. Shared Select now
scrolls its selected row into its own visible list. The catalog language filter adds
a styled search field matching localized names and codes, exact-code priority,
localized empty state, and keyboard selection without hijacking text-field Home/End.

Final isolated compiled UI passed RU/dark and EN/light at320/768/1366px:644choices,
Japanese/Arabic matching sets, search, empty Enter, Escape/reopen, Home/End and
selection, URL/reload, viewport bounds, no horizontal overflow, and a regular long
language menu in voice creation. There were no JavaScript errors or external requests.
The intermediate mobile-test failure came from querying the intentionally collapsed
filter panel after reload; the test now reopens it before verifying the visible control.
Before-fix, intermediate and final reports/screenshots are retained under
`catalog-language/`. Viewport screenshots were inspected, including320px and EN/light.

All64frontend tests pass, including all declared language codes, aliases, duplicate
localized labels and search. TypeScript/Vite build passes. Hallmark static lint reports
0FAIL/2WARN: selected states intentionally share a fill; shared form controls intentionally
share edges. The render tier remains unavailable without Puppeteer; actual Playwright
captures provide the browser evidence. Java and Python application sources did not
change in this checkpoint; their prior39/106test results retain their stated scope.

The verified UI was installed into the running local studio with new assets first and
an atomic index replacement last, retaining old hashed assets for already-open clients.
The previous client is backed up under `.runtime/releases/20261101T095656Z-catalog-languages`.
HTTP index SHA and referenced asset responses were verified; the Java JAR was not
overwritten or restarted. Full project documents/revisions/timestamps,4protected
profile files and77audio files remain unchanged. The exact idle QA server7089 was
stopped after checking its project and empty active queues. Full46-model release
approval remains withheld; external access and recorded quality/capability reviews
remain open.

### 2026-11-01: preserve selected speech when inserting markup

The compiled editor had a reproducible data-loss defect: inserting a pause into a
selection replaced the selected words. Both Fish emotion buttons used the same
replacement path. A proper before-test waited for the existing non-inert workspace,
selected `every word`, and observed those words disappear. An earlier harness filled
the inert loading workspace programmatically and is retained separately; it is not
evidence of a startup editing defect. The existing loading guard remains intact.

Shared speech-markup helpers now insert emotion tags before a selection and a pause
after it, preserving every original character. When the selected model uses SSML and
the source has a speak root, a pause becomes `<break time="500ms"/>` inside that root.
Insertion moves outside XML tag names, quoted attributes and comments; plain text
continues to use the shared application PCM pause syntax. This is editor support,
not an assertion that the externally unavailable Silero model has been tested.

All67frontend tests pass, including three focused markup tests. TypeScript/Vite
build passes. The isolated compiled UI passed RU/dark and EN/light at320/1366px:
pause and both emotion actions preserve selected words, actual server persistence
and reload retain the script, and four valid SSML locations per state remain valid
XML. Only the catalog GET was mocked for the unavailable Silero editor; no Silero
generation or download was attempted. Harness corrections waited for the prior
animation-frame caret restoration and drained mocked routes before closing contexts.
No product changes were made for those harness timing issues.

Actual unmocked Studio UI selected installed Kokoro, inserted a pause after selected
words, submitted the exact script, generated two speech parts, and restored the saved
script, model and new take after reload. WhisperLargeV3 and Qwen3-ASR both exactly
matched the expected words after normalization on the same WAV SHA256. A central
digital-zero run measures0.8938s, including the requested0.5s PCM pause and native
speech tails; it is not claimed as an exact spoken-boundary measurement. Reports,
before/final screenshots and audio remain under `markup-edit/`.

The verified client was published with assets first and an atomic index last;
previous client: `.runtime/releases/20261101T110541Z-speech-markup/previous-client`.
HTTP index and referenced asset hashes match. The running Java JAR was untouched;
all two project documents/revisions/timestamps,4protected profile files and77audio
files remain unchanged. The exact idle QA7090 server was stopped before the serial
ASR runs. Python and Java application sources did not change in this checkpoint.

A separate QA-only VibeVoice CFG-condition timing experiment did not resolve the
Large5s reference repetition and lost a word in a1.5B30s control. Both recognizers
agree on those defects. The prototype remains ignored QA code and was not shipped;
working adapters, weights and reference audio were unchanged. Full46-model approval
remains open for the existing access and quality limitations.

### 2026-11-01: independent lexical review and actual markup controls

GigaAMv3 screened ten disputed existing Russian long WAVs. All source hashes match
the original generation metrics; nothing was regenerated to chase a better score.
ChatterboxV3, VoxCPM2 and PiperIrina matched exactly. Seven other cases still differ;
GigaAM/Qwen-ASR agree on the QwenBase0.6B `и работу` → `работы` discrepancy. Third-ASR
agreement does not establish listening quality; the GigaAM adapter's20s chunk boundaries
can themselves introduce recognition errors. Original dual-ASR reports remain unchanged.

Six families completed sixteen real markup/delivery cases across root and independently
installed relocated runtimes: Fish inline whisper/laughing, ChatterboxTurbo sigh/chuckle,
Orpheus sigh/laugh, Dia alternating speakers/laughs, QwenCustomVoice whisper/excited and
VoxCPM2 whisper/excited. Twelve results exactly match both ASRs; two Orpheus cases are
recognizer disagreements; two Qwen whispers retain lexical review, including a possible
can/can't disagreement. Separate fixed-gain QA copies did not resolve those cases and
did not replace original recordings. Distinct delivery hashes/levels prove influence,
not emotional strength or distinct Dia identities. Each of eight corresponding root/
relocated pairs was byte-identical in this specific run. Reports: `expressiveness-controls/`.

The generation audit helper now accepts an optional emotion argument (default calm),
so these tests exercise the actual submitted control rather than rewriting model text.
The official Silero artifact still fails during certificate-checked TLS connection;
the bounded repeated HEAD attempt ended with curl28/SSL connection timeout. OpenAudio
still lacks legitimate local weights. Neither case is counted as successful inference.

### 2026-11-01: connect native IndexTTS delivery

Found an actual advertised-capability gap: Index's native SDK supports emotion vectors,
but the adapter ignored the existing request emotion. The adapter now maps calm to
native reference delivery (None), excited to happy and angry to angry. Other choices
fail before large weights load. The UI reuses the existing Delivery Select and offers
only those three choices. A model switch uses a supported effective delivery without
rewriting the stored scene setting; switching back restores that stored choice.
Saved takes derive their delivery label from their own model, not the active model.

The isolated prototype generated all three choices in both runtime installations;
all six WAVs exactly matched the expected words in WhisperLargeV3 and Qwen3-ASR.
The final compiled UI passed eight actual unmocked states: RU/dark and EN/light at
320/768/1280/1366px, viewport-safe menus, keyboard selection, no horizontal overflow,
no default desktop inspector scroll, source/unsupported-setting preservation across
model changes, and exact server persistence/reload. The actual UI also submitted,
generated and played an angry Index take, retained its original text/emotion after
later edits, and restored the edited draft separately on reload.

The original harness stopped after submission on an incorrect explicit-English assertion;
Index intentionally infers language and correctly submits auto. That same job was observed
terminal and reused, without duplicate generation. Post-completion edits were checked;
concurrent edits during generation are not claimed by this checkpoint. Although the
direct root/relocated pairs match, the UI WAV differs from the direct angry prototype
despite seed42. It received its own two exact ASR screens. No cross-launch byte identity
is promised. These harness/seed qualifications remain in `index-emotion-ui/`.

All108Python and70frontend tests pass, including native parameter forwarding, rejection
before loading, preserved unsupported scene delivery and model-specific historical labels.
TypeScript/Vite build passes. Hallmark static lint:0FAIL/2existing answered warnings;
render unavailable without Puppeteer. Actual desktop/mobile screenshots were inspected.
Java application sources did not change; its previous39tests retain their scope.

The verified client was published with retained old assets and atomic index replacement.
Backup: `.runtime/releases/20261101T115849Z-index-delivery/previous-client`, plus prior
Python adapter and catalog copy. Source changes in synthesis are limited to Index;
the two catalog edits only correct stale component-installation notes for Index/Higgs.
All two project documents/revisions/timestamps,4protected profile files and77audio files
are unchanged. The idle exact QA7091 server was stopped before serial UI-ASR verification.
Production Java was not restarted or overwritten. `docs/voice-controls.md` now describes
connected controls, model-specific markup and native features not exposed by this studio;
it does not turn untested native features or gated models into successful checks.

### 2026-11-02: full recording history and durable take choice

An isolated130-row history reproduced two actual defects. The old `/api/jobs` bootstrap
response intentionally contained only100rows, but the Library treated it as the full
searchable history. The oldest WAV/individual job were still accessible by ID while the
Library returned no search result. Project reconciliation also replaced an existing
selected take with newly linked jobs, and trimming links to100could evict the selected ID.

New `/api/recordings` searches every successful persisted result and returns bounded
6/12/24-item pages with a total, stable timestamp/ID ordering and validated parameters.
The recent100job bootstrap remains bounded. Library merges generated pages and available
local samples without changing global playback indices. Loading/error states distinguish
full results from cached rows; retry preserves audio. Stale delayed search responses cannot
replace the current query. Historical page reads register recordings without re-entering
the active-job reconciliation path. App reconciles each completed job once, avoiding a
repeated project-GET loop for archived IDs outside a compact scene snapshot.

Compact100-ID scene snapshots and conflict merges now retain the explicitly selected
recording. New jobs include a server-derived optional `selectionAtSubmission`, captured
after linking prior completed jobs. A new result follows that selection only when it still
matches; later manual changes win. Old metadata without the field remains readable and
conservatively preserves existing selections. First takes still select automatically.
This retains ordinary new-generation behavior instead of simply disabling auto-selection.

The fixture used131metadata rows referring to copies of one anonymous QA utterance;
these are not131neural inferences. One additional actual Piper job verified the new request
protocol, frozen source selection, default selection of its finished result, and unchanged
scene draft. WhisperLargeV3 exactly recovered its intended words. Full generated history
then had132items, plus three local padded anonymous samples:135Library results. All132IDs
were traversed without duplicates using each server page size before/after restart.

Actual compiled browser checks passed RU/dark and EN/light at320/768/1366px: old recording
search, pages, source/size filters, playback, paused seek, byte-identical downloads, available
samples on the final mixed page, reload and bounded project reads. A delayed-request test
used the real API with injected latency; the older response did not overwrite the newer
query. An injected503 showed cached-only wording, no false empty-history claim, and a
successful real retry. No external browser requests or JavaScript errors were observed.
Exact project document/revision/timestamps and the real job, including its new field,
survived a QA restart. The native range input is an implicit slider; an initial harness
used an incorrect explicit-role CSS selector and was corrected without changing the product
or re-generating the already completed job. Earlier harness evidence is retained.

All74frontend and42Java tests pass. The first sandboxed Java run could not bind its local
test server or inspect child processes; the permission-scoped rerun passed. TypeScript/Vite
build passes. Python application source did not change; the last108-test result keeps its
scope. Hallmark reports0FAIL/2existing answered warnings; its render tier lacks Puppeteer.
Actual desktop/mobile captures were inspected using the existing local browser runtime.

Deployment initially remained unapplied: automatic review rejected the combined rollout
and a separate production shutdown. The user then explicitly authorized “Да, перезапустить
и установить”. A separate approved step stopped and verified exit of idle PID46302 before
any JAR replacement. The stopped installation backed up the old server/client and cloned
data/outputs locally, then started the supported server entry point. New production PID75019
serves4173. Backup: `.runtime/releases/20261102T051502Z-history-retention`.

Post-start HTTP/JAR/asset hashes match the verified candidate. All two project rows,
project-job links,4profile files,77output files and30job documents are unchanged;28successful
recordings are reported by the new production endpoint. The catalog remains46entries,
44ready. No user browser/storage was manipulated, no model dependency/weight changed,
and the exact idle QA7092server was stopped. Full-model release approval remains open for
the separately recorded author-access and quality limitations.


### 02.11.2026: полная история улучшения аудио

Устранён отдельный предел истории очистки: прежний bootstrap API возвращал
последние 100 задач, а поиск и страницы работали только с этим массивом.
Файлы не удалялись, старая прямая ссылка открывалась, но поиск не находил
ранние версии. Добавлен `/api/cleanups/history` с серверным поиском по названию,
нормализацией регистра/«ё», ограниченным размером страницы и стабильным порядком.
Прежний `/api/cleanups` сохранён для состояния последних/активных задач.

Интерфейс получает страницы отдельно, регистрирует найденные задачи для выбора
и сравнения, игнорирует запоздалые ответы старого поиска. Ошибка истории
показывает повтор загрузки, а не ложное отсутствие записей. Фоновое обновление
не сбрасывает текущие настройки улучшения и не прячет список при каждом опросе.

Изолированная QA-база: 130 синтетических строк очистки с копиями одного
анонимного QA WAV; это проверка хранения/интерфейса, не 130 нейросетевых задач.
Все ID получены без повторов на страницах 6/12/24; старейший результат и оригинал
имеют ожидаемые хэши. В браузере проверены RU/dark и EN/light на 320/768/1366px,
поиск, выбор, воспроизведение/перемотка, A/B-позиция, неизменность черновых
настроек при поиске и открытие по URL после перезагрузки. Проверены задержанный
ответ прошлого запроса и HTTP 503 с повтором. Первый браузерный прогон остановил
неоднозначный селектор двух заголовков теста; селектор уточнён, исходный отчёт сохранён.
Новых ошибок JS и внешних запросов нет. Java: 43/43; frontend: 74/74. Python
и нейросетевая обработка не менялись. Журналы: `.runtime/release-audit/cleanup-history/`.

Повторное открытие уже очищенного дубля учитывает его модель, даже когда задача
старше bootstrap-списка: открывается сохранённая версия по ID без новой обработки.
Это отдельно проверено из студии в QA-проекте; новых POST-задач не отправлено.
Все 130 версий и их порядок сохранились после настоящего перезапуска QA API.

Исправление установлено с явным разрешением на перезапуск. Рабочий API остановлен
до замены JAR; резервная копия: `.runtime/releases/20261102T053833Z-cleanup-history/`.
Первая попытка установки остановилась до замены файлов из-за ошибки открытия SQLite
через URI. Соединение по обычному пути и SELECT подтвердили доступность базы.
После установки сравнение обеих таблиц проектов и 151 защищённого файла
подтвердило неизменность данных. Новый API PID 77668, `/api/health` ready,
новый маршрут возвращает четыре существующие пользовательские версии. Все HTTP-ассеты
совпадают со сборкой; прежние хэшированные ассеты оставлены для открытых вкладок.
Временный QA API остановлен. Код Python и модели это обновление не меняет.

### 02.11.2026: Silero: официальный источник восстановился

Повторный HEAD официального `v5_6_ru.pt` завершился HTTP 200, Content-Length
147664410. Модель установлена штатным API каталога в рабочий проект, затем
повторно скачана в отдельный пустой кэш. Оба полных файла имеют SHA-256
`04cc9b1d08ce38bcaa9d02c488d80d3e6806d17f7eaa7c95982f36a3cbf50b2e`.
Теперь размер и хэш закреплены в каталоге вместо динамического манифеста;
для новых установок доступны известный размер/процент и проверка хэша.
Изменена только запись Silero. HTTPS-сертификаты проверялись, зеркал нет.

Настоящий синтез выполнен в рабочем и независимо установленном перенесённом
окружении с профилем macOS sandbox, запрещающим сеть. Отдельная попытка
сетевого соединения этим профилем завершилась PermissionError. Короткие
результаты обоих окружений совпали по SHA-256. Измеренный RSS 1.00/1.01 ГиБ
не включает всю систему/браузер и не является минимальным требованием к RAM.
Все пять голосов также синтезировали тестовую фразу без сети.

Проверены семь дополнительных сценариев: SSML-паузы 500/1500ms, slow/fast,
высота high, знак ударения `+`, длинный русский текст с `[pause:1.25]`.
Разница длительности SSML-версий: 1.0000000000000004 с; slow длиннее fast.
В длинном WAV 48000 Гц есть ровно 60000 подряд нулевых отсчётов, длительность
40.295 с. Ударения/высота приняты моделью; измерения не удостоверяют субъективно
правильное ударение и натуральность каждого слова.

Из отдельного QA-интерфейса создан настоящий дубль: Silero → xenia → SSML
с паузой, вставленной кнопкой редактора. Текст и голос пережили перезагрузку,
плеер воспроизводит/перематывает результат. Проекты и выбор Fish рабочей студии
не менялись. Совокупно проверены 15 настоящих WAV; в 14 словесный текст точно
совпал у Whisper Large V3 и Qwen-ASR. Длинный WAV требует лексической проверки:
Whisper добавил «Продолжение следует», Qwen иначе распознал «ошибку», GigaAM:
фрагмент «Перед добавлением». Исходник/хэш сохранялись между ASR-прогонами;
перегенерации ради совпадения не было. По отдельным разногласиям не делается
вывод об идеальной речи либо установленной ошибке синтеза.

108 Python-тестов прошли после уточнения контракта каталога: для URL проверяется
HTTPS и закреплённый SHA-256, для Hugging Face: 40-символьный commit hash.
Первый прогон выявил прежнее требование commit hash даже для прямого URL;
его журнал сохранён. Код Java и интерфейс этим изменением не затрагивались.
Текущий каталог: 46 моделей, 45 готовы; 0 структурных ошибок. Все существовавшие
151 файл данных и строки проектов совпали с резервной копией. Добавился только
служебный документ успешной установки Silero. QA API 7094 остановлен;
рабочий API 4173 продолжает работать с прежним JAR.

Журналы: `.runtime/release-audit/current-access-check/`, `silero-root/`,
`silero-relocated/`, `silero-fresh-download/`, `silero-controls/`, `silero-screening/`.
Доступ OpenAudio S1 Mini по-прежнему требует принятия условий аккаунтом автора
запроса на Hugging Face; вход/принятие условий и обход доступа не выполнялись.
Полная проверка всех 46 моделей остаётся незавершённой.

### 02.11.2026: начат полный прогон скачивания в независимый пустой кэш

Сводка прежних установщиков выявила 14 исходно кэшированных моделей: у них
были реальные WAV/проверки хэшей, но этих данных недостаточно для полного
доказательства установки из сети новым пользователем. Неудачные старые попытки
остаются в журналах, последующие успешные повторы учитываются отдельно.

`scripts/verify-model-downloads.py` получил явный `--artifact-root` для отдельного
кэша весов внутри проекта. Этот режим не переустанавливает окружения: они
проверены собственным полным установщиком и перенесёнными окружениями.
Загрузчик остаётся тем же `models.download`, проверяет закреплённые размеры/хэши;
выбор модели, профили и рабочий кэш не меняются. В отчёте сохраняются путь,
хэши каталога/установщика и результат каждого процесса. CLI отвергает выход
кэша за проект и ссылки на рабочие каталоги моделей.

Начальное отсутствие нового кэша записано до старта в
`.runtime/release-audit/cold-catalog/origin.json`. Все 45 доступных моделей
распределены между тремя последовательными установщиками с отдельными журналами
и одним новым кэшем; общий объявленный размер 132418655421 байт (123,32 ГиБ,
общие зависимости могут переиспользоваться внутри этого нового кэша).
OpenAudio сохранена в общем перечне как требующая разрешённых весов, её доступ
не обходится. Папка нового кэша не связана с рабочими blob-файлами.

Это работающий длительный прогон, а не законченная проверка. Результаты нужно
читать из живых процессов/`downloads.json`; файл с PID сам по себе не доказывает
работу процесса. Подготовлена отдельная копия исходников и ссылки на ранее
независимо установленные окружения для последующего синтеза с новыми весами.
Проверка нового скачивания сама по себе не доказывает успешный инференс.

### 02.11.2026: родная разметка OpenAudio и мобильная подсказка

Страница автора S1 Mini показывает круглые скобки `(angry)`, `(excited)`,
`(whispering)`, `(laughing)`. В каталоге раньше стоял общий тип `fish`, а редактор
показывал общую подсказку. Выделен тип `fish-legacy` с точной RU/EN-подсказкой
в разметке и расширенных настройках. Изменена только запись gated OpenAudio;
все 45 скачиваемых записей, URL, размеры и хэши остались прежними. Источник: [карточка автора](https://huggingface.co/fishaudio/s1-mini). Это сверка документации и UI,
а не подтверждённый инференс модели без весов.

Проверка скриншотов обнаружила обрезанную подсказку паузы на 320px: поздний
CSS-override привязывал её правым краем к кнопке. Привязка перенесена к панели
редактора, ширина ограничена панелью. Дополнительно убрано наследование nowrap
от кнопки; первая геометрическая проверка рамки не выявляла выход самого текста,
поэтому добавлен контроль переноса и визуально проверен весь текст. Доступное
имя кнопки остаётся коротким и стабильным при показе подсказки.

Реальный QA API использовал отдельную БД. Для шести состояний OpenAudio готовность
явно подменена только в браузерном каталоге: RU/EN, 320/768/1366px, вставка паузы
с сохранением слов, родные теги, расширенные настройки на ПК. Новых заданий нет;
реальный API продолжал считать OpenAudio недоступной. Ещё два мобильных состояния
проверены с настоящим каталогом Fish, где перед паузой есть кнопка акцента.
Восемь состояний прошли; JS-ошибок нет. Проверки: frontend 74/74, Python 108/108,
Hallmark 0 FAIL и два прежних объяснённых предупреждения. CSS-рендер Hallmark
не запускался, использованы реальные Playwright-снимки.

Клиент установлен атомарно без перезапуска API, PID 77668 и JAR не изменились.
Резервная копия: `.runtime/releases/20261102T065734Z-openaudio-markup-tooltip/`.
152 защищённых файла, строки проектов и связи заданий совпали до/после установки.
Старые ассеты сохранены для открытых вкладок. QA API 7095 остановлен.
Журналы: `.runtime/release-audit/openaudio-markup/`.

### 02.11.2026: промежуточные результаты нового кэша

Скачаны четыре Piper, OpenVoice, Whisper Base/Small и Silero; остальные очереди
живы и продолжают реальную передачу. Перед каждой новой нейросетевой задачей
контроллер проверяет отсутствие активных задач рабочей студии, затем запускает
одну задачу с запретом сети. Восемь первых моделей выполнили задание в перенесённых
окружениях с новыми весами. Проверены 28 файлов: хэши новых файлов совпали с
закреплёнными значениями/соответствующими проверенными рабочими файлами.

Пять из шести новых речевых WAV точно распознаны Whisper Large V3. В коротком
Piper Ruslan оба ASR, Whisper и Qwen, пропустили «и» в «ясно и естественно».
Исходный текст и WAV не менялись; это отмечено для прослушивания, не скрыто
перегенерацией. Непустой ASR-транскрипт: технический успех, а не гарантия
дословности. Например, новая Whisper Base также ошибается в контрольном эталоне.
Отдельно сопоставлены имеющиеся реальные RU-результаты девяти ASR в двух
окружениях с заданным текстом синтетического эталона: `.runtime/release-audit/asr-quality/`.
Без независимой ручной расшифровки эталона это различия с заданным сценарием,
а не сертифицированный WER и не общий рейтинг ASR: ошибаться могла и TTS.

Полный независимый прогон скачивания остаётся незавершённым; живые сессии и
результаты находятся в `.runtime/release-audit/cold-catalog/`. Отдельные HTTP
соединения обрывались, библиотека продолжала загрузку Range-запросами; эти логи
сохранены. Нельзя приравнивать наличие прогресса/части файла к успешной установке.

### 02.11.2026: черновики инструментов моделей

В реальном интерфейсе OpenVoice воспроизведена потеря выбранного файла:
открыть инструмент, выбрать WAV, перейти в «Голоса» и вернуться: инструмент
закрывался, локальный state исчезал. Первый тестовый селектор ожидал другое
название кнопки; после сверки фактической подписи воспроизведение подтвердило
нулевое число рабочих панелей после возврата, без запуска обработки.

Черновики вынесены в session-only hook приложения, раздельно по ID модели.
Сохраняются File, описание, длительность, выбранный профиль, загрузка, ошибки
и ID задания. Серверные задания/файлы не переписываются. Закрытие панели скрывает
её, а выбранные данные остаются до очистки или закрытия/перезагрузки страницы.
При возвращении виден результат фонового задания. Позиция прослушивания хранится
в ref без перерисовки всего приложения на каждом аудиокадре; уход с вкладки
останавливает локальный плеер, возвращение сохраняет его позицию без автозапуска.

Проверка с настоящей конвертацией OpenVoice на API 7096 и новыми весами: WAV
пережил переходы, реальная загрузка/обработка завершились, после возврата появился
результат; перемотка, остановка невидимого аудио и восстановление позиции прошли.
Отдельный API 7097 с проверенными рабочими весами подтвердил шесть RU/EN-состояний
на 320/768/1366px: File OpenVoice и текст/длительность MOSS не смешиваются между
моделями и сохраняются между вкладками. Из UI выполнен настоящий MOSS SoundEffect
без voiceId/sourceId: 1.0 с, PCM16 mono 24000 Гц, RMS −30.92 дБ, без клиппинга.
Это техническая проверка результата, не субъективная оценка соответствия описанию.
JS-ошибок нет; TypeScript и 74 frontend-теста прошли. Код Java/Python не менялся.

Клиент установлен без перезапуска API. PID 77668/JAR прежние, 152 защищённых
файла и строки проектов совпали до/после. Резервная копия:
`.runtime/releases/20261102T075856Z-workbench-drafts/`.
Журналы: `.runtime/release-audit/workbench-drafts/` и
`.runtime/release-audit/cold-catalog/tool-draft-before.json`.

### Промежуточная холодная установка: обнаружены транспортные ошибки

На следующем срезе 19 скачиваний завершились успешно. Whisper Turbo, Whisper Medium
и Resemble Enhance завершили конкретные попытки с `httpx.ReadError`, errno54,
connection reset by peer. Частичные данные сохранены, модели с незавершённой
проверкой не объявляются установленными. Очереди продолжили другие модели;
повтор этих трёх возможен после терминальных ошибок без остановки живых очередей.
Нужно отдельно проверить восстановление передачи и ограниченные повторы ошибок
чтения: прежняя проверка кэша такие ошибки новым пользователям не показывала.
Ни весь холодный прогон, ни все 46 моделей этим срезом не подтверждены.


### 02.11.2026: восстановление скачивания после сетевого обрыва

Три реальные попытки холодной установки выявили `httpx.ReadError`, errno54.
Добавлены максимум три попытки передачи одного файла с паузами 1 и 2 секунды.
Повтор использует тот же локальный кэш/частичный файл; проверка закреплённого
размера и SHA-256 остаётся обязательной. Незавершённая проверка сохраняет pending
и не делает модель доступной для выбора. Для прямого HTTPS-источника проверяется
начало Content-Range; короткий ответ сохраняется как .part и дозагружается.
Ошибки 401/403/404, проверки сертификата, некорректного каталога и переполнения
диска не повторяются; проверка TLS не ослаблялась, токены не запрашиваются.

Пять новых тестов: реальный обрыв локального HTTP-ответа с продолжением Range
с байта 1100000 и проверкой хэша; обрыв Hub с сохранением частичного файла;
исчерпание трёх попыток; запрет повторов постоянных ошибок; отклонение файла
верного размера с неверным хэшем. Полный Python-набор: 113/113. Исправление
установлено атомарной заменой модуля; Java и frontend не менялись. Рабочий API
подтвердил 46 записей/45 ready, прежние выбранные Fish и Whisper Small;
JAR и index.html имеют прежние хэши. Резервная копия исходника и журналы:
`.runtime/release-audit/download-resume/`.

Живые очереди загрузки не перезапускались. Старые дочерние процессы продолжают
с загруженной версией модуля; новые события содержат installerSha256, вычисленный
при импорте, чтобы не приписывать им исходный хэш родительского отчёта.
Три терминальные ошибки повторяются в отдельном отчёте retry-transfers с тем же
физическим независимым кэшем. Whisper Turbo успешно завершила повторную попытку;
первоначальная ошибка сохранена. Срез checkpoint: 25 полных загрузок и 24
реальные задачи без сети. Это промежуточные результаты, а не подтверждение всех
45 установок с нуля или всех 46 моделей. Доступ OpenAudio остаётся отдельным
внешним условием; пользовательские записи в этой проверке не использовались.


Следующий срез: Whisper Medium также успешно докачана; Resemble продолжает
повторную передачу. Полные новые загрузки: 27; офлайн-задачи: 26. Новые результаты
19 речевых моделей проверены Whisper Large v3 и Qwen-ASR: у 18 точное совпадение
нормализованного текста в обоих ASR, у Piper Ruslan оба не распознали «и».
Первый WAV не заменялся повторной генерацией для улучшения отчёта; разные SHA
этой модели в прежних прогонах сохранены. Это отдельная проверка, не ретроактивное
изменение прежних точных результатов. Для семи новых ASR сохранены различия
с заданным текстом анонимного синтетического эталона, а не сертифицированный WER:
`.runtime/release-audit/cold-catalog/asr-script-review.json`. Ручной независимой
расшифровки нет; дефект могла внести и исходная синтетическая запись.

К концу этого среза: 28 новых загрузок, 27 офлайн-задач; Whisper Medium прошла
реальное распознавание. Parakeet завершила скачивание и ожидает следующего
последовательного запуска. Три исходные очереди и отдельный повтор Resemble
продолжают работу; они не останавливались по окончании наблюдения.


### 02.11.2026: реальная отмена и продолжение установки через интерфейс

В `.runtime/release-audit/download-resume-ui/` создана третья изолированная
установка: собственные БД/задания, физически отсутствовавший кэш, текущие исходники,
копия проверенного JAR и ранее отдельно установленное перенесённое окружение.
Это проверка нового кэша модели, а не повторный bootstrap всех зависимостей.
В браузере без подмен каталога/файлов запущена установка официального Piper Dmitri.
После начала передачи нажата отмена. Сохранён .incomplete размером 10485760 байт;
модель не ready, кнопка: «Продолжить». Остановлен только QA API7098, затем
запущен с той же БД. Частичный файл и состояние отмены пережили перезапуск.

Через UI нажато продолжение. Полная установка завершилась, закреплённые размеры
и SHA-256 обоих файлов проверены отдельно. Выбор модели сохранился после reload.
Из UI создан настоящий дубль efbd95c1-1fab-45c7-999c-5757e5d96f32: 4.830 с,
PCM16 mono 22050 Гц, RMS −18.76 дБ; текст/дубль пережили reload, воспроизведение
и перемотка прошли. Оба ASR подтвердили слова и отличаются только «создаётся» /
«создается»; строгие исходные статусы review сохранены. JS-ошибок нет. Рабочие
проекты не использовались, выбор Fish/Whisper в рабочей установке не изменился.
Тестовый сервер завершён; рабочий API4173 не перезапускался. Журналы/PNG/хэши
и summary.json находятся в указанной папке.

Все три повторные передачи Whisper Turbo/Medium/Resemble завершились успешно;
первоначальные ReadError не удалены из исходных отчётов. В независимом кэше
на текущем срезе 30 моделей завершили реальные задачи без сети. Все девять ASR
выполнили распознавание; это техническая проверка одного эталона, не общий рейтинг
точности. Из 21 речевого/обработанного WAV оба ASR точно подтвердили 20;
Piper Ruslan остаётся лексической проверкой. Три исходные очереди подтверждены
живыми по тем же сессиям, не перезапускались. Каталог из 46 целиком ещё не принят.


### 02.11.2026: закрытый потребитель прогресса и ещё два холодных запуска

Расширенный тест показал: BrokenPipeError при закрытии канала прогресса попадала
в общий ConnectionError и вызывала три попытки вместо одной. Исходный провал
сохранён в download-resume/closed-progress-before.log. Сырой BrokenPipeError теперь
не вызывает повтор передачи. Транспортные ошибки HTTP-клиента продолжают
обрабатываться отдельно. Расширенные пять сценариев и полный набор 113 Python
прошли на кандидате; установленный модуль повторно прошёл сценарии передачи.
Модуль заменён атомарно, резервная копия сохранена. Текущий хэш установщика:
c1248ac41d6191756820d031a0eccc1ca3db6b51f030397354444eb8061e93ce.
Новые дочерние процессы указывают свой хэш; старые живые загрузки не прерывались.
Настоящий UI-сценарий отмены/продолжения выше относится к предыдущему хэшу
251af4d9da528a60a100c004e71fd37177a25348914261059395b90c54946dec;
изменение BrokenPipe подтверждено отдельным тестом, а не приписано этому UI-прогону.

CosyVoice3 и Parler Mini завершили реальные офлайн-задачи в независимом кэше.
Оба ASR точно подтвердили слова новых записей. Срез: 32 загрузки/32 задачи;
из 23 речевых результатов оба ASR точно подтвердили 22, один Piper Ruslan
остаётся проверкой на слух. Все девять ASR технически завершили одну и ту же
задачу распознавания; word edits относительно сценария сохранены отдельно.

В журнале CosyVoice найдено общее предупреждение Transformers4.57.6 о Mistral.
У закреплённой модели model_type=cosyvoice3, tokenizer_class=Qwen2Tokenizer,
нет transformers_version. Локальная эвристика не отсекает такой config.
Regex tokenizer.json точно совпал с [исходным Qwen2](https://github.com/huggingface/transformers/blob/v4.57.6/src/transformers/models/qwen2/tokenization_qwen2.py);
причина предупреждения проверена в [эвристике Transformers](https://github.com/huggingface/transformers/blob/v4.57.6/src/transformers/tokenization_utils_base.py).
В 20 локальных примерах текущий fast-tokenizer дал те же ID, что исходный slow
Qwen2, а явное fix_mistral_regex=False не меняло ID. Принудительный True изменил
один пример, поэтому Mistral-правка не включена. Это проверка данного токенизатора,
а не подтверждение произношения на всех языках. Первый запуск slow-пробы не
нашёл отдельные vocab/merges: модель хранит самодостаточный tokenizer.json.
Для контрольной пробы они извлечены только в QA-папку; файлы модели не менялись.
Журналы: cosy-tokenizer-warning/, включая исходную ошибку конструкции пробы.

Итоговая проверка рабочей установки сравнила строки проектов/связей и хэши всех
152 файлов data/outputs с резервным снимком последнего релиза: всё совпало.
JAR и index.html прежние. Проверка сохранности:
download-resume-ui/production-preservation.json. Рабочий API не перезапускался;
QA API7098 остановлен после проверки. Полный каталог из 46 ещё не принят.


### 02.11.2026: холодные Dots MeanFlow, LongCat и Chatterbox Multilingual

После подтверждения живых прежних очередей новые модели последовательно выполнили
реальные офлайн-задачи в том же независимом кэше. Проверены валидный непустой WAV,
сохранность артефактов и ready после запуска. Все три неизменённых WAV точно
совпали с заданным текстом по нормализации Whisper Large v3 и Qwen3-ASR.

Срез: 35 доступных моделей скачаны и прошли задачу. Из 26 речевых результатов
оба ASR точно подтвердили 25; предыдущий Piper Ruslan остаётся review. Эти
результаты не заменяют проверку натуральности/тембра и длинных сценариев. Десять
доступных моделей ещё в очередях, OpenAudio остаётся отдельным gated-случаем.
Сессии 45038/80149/71216 и PID80616/80607/80598 продолжаются; очереди не
перезапускались. События новых Dia/FireRed/MOSS указывают текущий хэш установщика
c1248ac41d6191756820d031a0eccc1ca3db6b51f030397354444eb8061e93ce.
Журналы: cold-catalog/ready-progress-mf-longcat.log,
ready-progress-chatterbox.log и screen-mf-longcat-chatterbox.log. Новых изменений
рабочего Java/frontend/Python в этом срезе не было; прежние 113 Python, 74 frontend,
43 Java относятся к установленным версиям. Каталог из 46 не объявлен готовым.


### 02.11.2026: сверка исходных артефактов и третья ASR для Piper Ruslan

Новый read-only verifier сопоставил текущие WAV/PCM-метрики/SHA-256 с исходными
inference.json, ID/длительности/sampleRate завершающих событий с заданием,
состояние ready и хэши WAV во всех отчётах ASR. Ожидаемый текст повторно выведен
из исходного задания, статусы screened/review пересчитаны из сырых строк;
успешные загрузки имеют exitCode0 и завершающее событие installed. На срезе
35 моделей противоречий не найдено. Это целостность исходных доказательств,
а не субъективная оценка качества или приёмка всех 46. Файлы:
cold-catalog/verify-evidence.py и evidence-integrity.json.

GigaAM v3 дополнительно проверила прежний, неизменённый WAV Piper Ruslan
SHA d5ec0e41094f9d21ee5517a75deac9b170a9dc4b5891ba8c95e15536d53a1b2c.
Как Whisper и Qwen, она не распознала союз «и» между «ясно» и «естественно».
Оценка остаётся review. Штатный EspeakPhonemizer с тем же голосом ru выдаёт
разные последовательности для текста с союзом и без: в первом есть отдельная
безударная гласная ɪ. Все фонемы имеют ID в конфигурации модели, включая эту
гласную. Приложение передаёт исходный текст в Piper.synthesize; удаление слова
до нейросети не обнаружено. Это локализует проверку, но не доказывает на слух
точную причину расхождения: TTS или распознавание. Исходник не заменён и не
перегенерирован ради совпадения. Файлы: model-transcripts-gigaam-v3.json,
ruslan-gigaam.log, ruslan-phonemes.json и соответствующие скрипты в cold-catalog/.


Dia завершила холодную загрузку и реальную офлайн-задачу. Оба ASR точно подтвердили
текст нового неизменённого WAV. Срез: 36 загрузок/задач, 27 речевых результатов,
из них 26 точных совпадений двух основных ASR и один прежний review Piper Ruslan.
Verifier доказательств теперь явно сохраняет недостающие модели и покрытие ASR;
GigaAM отмечена диагностическим подмножеством, а не полным третьим прогоном.
Завершение одной проверки целостности не означает полноту всего каталога.

В frontend/AGENTS.md исправлена устаревшая формулировка «пять вкладок»: покрытие
требуется для каждой вкладки, включая Cleanup, и обоих режимов редактора.
Поведение/стили приложения не менялись. Прежние реальные сценарии на 1920px
имеются в relocation-visual.cjs, catalog-ui/workbench-responsive.cjs и
japanese-normalization/responsive.cjs; наличие этих сценариев не приписывает
новому срезу повторный рендер всех состояний.

### 02.11.2026: все доступные веса скачаны, все 45 моделей прошли UI

Три первоначальные очереди завершились без перезапуска. С учётом отдельных
успешных повторов Whisper Turbo, Whisper Medium и Resemble все 45 доступных
моделей скачаны в изначально пустой физически отдельный кэш. Внутренние ссылки
Hugging Face ведут только к его собственным blob-файлам. Исходные три неудачные
попытки сохранены; их пакетные отчёты не переписаны в успешные. Для отдельных
новых дочерних установщиков сохранён хэш использованного кода.

Через отдельный Java API7099 и настоящий браузер выполнены все 45 маршрутов:
33 варианта синтеза, 9 распознавателей, OpenVoice, MOSS SoundEffect, Resemble.
Использованы заново скачанные веса и ранее независимо установленные перенесённые
окружения. Это не повтор установки каждого окружения для каждой модели.
Для каждого синтеза проверены выбор модели/профиля или встроенного голоса,
настоящий POST, успешное серверное задание, сохранение текста/модели после
перезагрузки, проигрывание и перемотка. Все девять ASR прошли подготовку
анонимного образца, сохранение, перезагрузку, прослушивание и удаление профиля.
Сохранение сырого ASR-черновика проверяет маршрут, а не правильность распознавания.

Дополнительный полный сценарий создал новый профиль, использовал его в реальном
синтезе Qwen Base 0.6B и удалил. Готовый дубль сохранил те же байты и проигрывался
после удаления профиля. В тестовой установке остались только два анонимных
исходных профиля. MOSS SoundEffect отправлялась без исходника и voiceId; у
Resemble проверены фактические этапы denoise/restore/mastering, неизменный
исходник и сохранение позиции при A/B.

37 WAV сверены с серверными ID/моделью, хэшем, длительностью и sampleRate.
Звуковой эффект исключён из речевой сверки: Qwen-ASR точно подтвердил все
36 речевых записей, Whisper: 35. В OpenVoice Whisper услышал “I'm” вместо
“I am”, Qwen совпал с исходным текстом. Строгий review сохранён. Предыдущий
прямой Piper Ruslan пользователь прослушал и сообщил «все отлично слышно»;
это оценка конкретной записи, исходные расшифровки трёх ASR не заменены.

Отдельный визуальный постконтроль очистки: 8 состояний RU/dark и EN/light
на 320/768/1366/1920px, переносы текста, отсутствие горизонтального выхода,
равная высота панелей при расположении рядом. Предположение об обрезанном
подвале снимка не подтвердилось DOM-измерением; CSS не менялся. Консолидатор
сначала излишне запрещал штатные внутренние HF-ссылки; проверка исправлена
на запрет выхода за независимый кэш. Это ошибка проверочного сценария, не
дефект установки модели.

Итоговый read-only verifier подтвердил соответствие всех 45 загрузок и
UI-маршрутов, неизменность WAV и исходных ASR-строк. Сравнение с резервным
снимком последнего релиза подтвердило те же 2 проекта, 12 связей заданий и
все 152 защищённых файла. JAR/index.html совпали с проверенными, рабочий API
не перезапускался. QA API7099 остановлен. Новый прямой Python-прогон остаётся
отдельной когортой из 38 задач; 45 UI-задач не маскируются под её события.

Журналы: cold-ui/results.json, asr-results.json, tool-results.json,
voice-roundtrip-results.json, inference.json, model-transcripts-*.json,
postflight.json, verified-summary.json, verify-summary.log; cold-catalog/
checkpoint.json и evidence-integrity.json. Изменения этого этапа: проверочные
сценарии и документация. Прежние 113 Python / 74 frontend / 43 Java относятся
к тем же установленным версиям продукта, повторных изменений приложения нет.

Весь каталог из 46 не принят: OpenAudio требует законных весов автора;
известные ограничения длинных/коротких эталонов и субъективная оценка голоса
остаются отдельными вопросами. Положительные короткие контрольные записи
не отменяют прежние результаты и не сертифицируют Windows/Linux или 8 ГБ.

### 02.11.2026: удаление OpenAudio по решению пользователя

По явному запросу удалена OpenAudio S1 Mini: запись каталога, отдельный адаптер,
ветка синтеза, recipe/lock и source archive, установленное окружение fish-legacy,
его исходники и подсказки RU/EN. Модельные веса отсутствовали. Удалены три
локальных runtime/source пути с прежним выделенным объёмом около 1 ГБ; общий
Python, общие кэши и Fish S2 Pro сохранены. Остальные 45 манифестов побайтово
эквивалентны прежним JSON-записям. Старые отчёты о закрытом доступе не стирались.

Повторно прошли 113 Python и 74 frontend, TypeScript/build и четыре реальных
UI-состояния RU/EN × 320/1366px: в каталоге 45 готовых моделей, в селекторе
33 варианта синтеза, OpenAudio отсутствует, поиск и размеры корректны.
Первые попытки QA обнаружили только ошибки подготовки самого стенда: тесты
поставки запускались до сборки, затем не был добавлен путь каталога; мобильный
сценарий не раскрывал настройки. Стенд исправлен, исходные журналы сохранены.
Сборка выполнена прямыми локальными командами TypeScript/Vite/prepare-sites-build
после отказа pnpm запускать сборку без проверки зависимостей в скопированной папке.

Проверенный frontend установлен атомарной заменой index.html после assets.
Java JAR и PID77668 не менялись, API не перезапускался. До/после совпали оба
проекта, связи заданий и все 152 защищённых файла data/outputs. Рабочая выбранная
модель: Fish S2 Pro. QA API7099 остановлен. Документация и перечень лицензий
обновлены; старые матрицы из 46 моделей описывают прежний каталог.

Журналы: .runtime/release-audit/remove-openaudio/; резервные исходники и интерфейс:
.runtime/releases/20261102T115412Z-remove-openaudio/. Новый index SHA-256:
889789b39f04a2f3a94253146dc02103e3e06375a5b4b0d7d5817338398a8c9b.

### 02.11.2026: состав публичных исходников

Проверены cached/untracked nonignored кандидаты только папки этого проекта,
включая содержимое шести архивов native-зависимостей. Характерных секретов,
личных путей/имён, аудиофайлов, модельных весов и баз не найдено; крупных файлов
свыше 10 МБ нет. Git родительского workspace пока не содержит коммитов и
отслеживаемых файлов этого проекта; публикация общего workspace не проверялась.
Его нельзя смешивать с отдельным репозиторием студии.

Усилен .gitignore для env/ключей, дополнительных аудиоформатов, весов, SQLite,
журналов и сборочных кэшей. Из кандидатов исключены два корневых Vite-cache JSON
и генерируемый из старых локальных демо frontend/src/audio-data.json. Последний
не удалён с устройства: import.meta.glob делает его необязательным, а в чистом
checkout примеры пусты. Веса, исходные записи, профили и проекты не менялись.

Отдельно собраны публичный вариант без манифеста и локальный с ним:
оба прошли TypeScript/Vite/подготовку Sites и по 74 frontend-теста. Новый Java
QA API7099 использовал отдельные пустые data/cache: реальный UI RU/EN на
320/1366px подтвердил 45 доступных к установке моделей, ноль установленных,
профилей и записей, отсутствие запросов к личным demo WAV. Это проверка чистой
поставки интерфейса, не новый полный прогон установки ML-зависимостей.

Подготовлен архив из явного списка Git-кандидатов с анонимными tar uid/gid,
пустыми uname/gname и проверкой содержимого/хэшей. Он не включает runtime,
соседние проекты, временные QA-данные или node_modules стенда. Это проверка
публикации и ограниченный поиск секретов, не полный vulnerability scan.
Журналы находятся в .runtime/release-audit/publication/; рекомендации:
docs/publication.md. Внешняя публикация/создание репозитория не выполнялись.

### 02.11.2026: согласованная очистка локальной установки

По запросу пользователя удалены локальные веса 42 ненужных моделей, девять
неиспользуемых дополнительных окружений, большие тестовые установки/копии,
ненужные download-кэши и старые резервные сборки. В каталоге сохранены все
45 записей, исходники адаптеров, locks/recipes и исходные native-зависимости.
Их можно установить снова. Поддержка Windows/Linux зафиксирована как отдельный
будущий этап; текущая поддержка остаётся macOS/Apple Silicon.

Локально оставлены Fish S2 Pro, Whisper Small и Resemble Enhance с основной
.venv и torch-audio. Все 12 требуемых файлов этих моделей сохранили SHA-256.
При удалении общего HF blob pool сохранены реальные цели всех ссылок оставшихся
репозиториев; окружения проверены на отсутствие ссылок в удаляемые каталоги.
Итоговые 371 JSON-отчёт, чистый архив исходников и проверка до/после сохранены
в .runtime/maintenance/cleanup-20261102T123832Z/ и .runtime/releases/public-source/.
Сырые тестовые WAV, окружения и staging-копии из прежних журналов больше
не находятся на диске; исторические статусы не означают их текущего наличия.

После удаления все три модели снова выполнили настоящие задачи с запретом сети:
Fish: озвучку, Whisper: распознавание, Resemble: обработку записи.
Проверочные аудио/окружение затем удалены, сохранены только небольшие отчёты.
Сравнение до/после подтвердило те же 2 проекта, 12 связей заданий и 156 защищённых
файлов, включая локальные образцы и их манифест. Замер du: вся папка около
12,1 ГБ вместо прежних 348 ГБ; APFS и системная активность могут давать иной
прирост свободного места, чем разница этих каталогов. Рабочие данные и исходники
не удалялись, студия запускается стандартным scripts/studio.sh.

### 04.11.2026: двуязычная документация и анонимные иллюстрации

Главный README теперь на английском с прямой ссылкой на README.ru.md. Добавлены
парные руководства установки, работы, моделей, данных, ошибок, разработки и
статуса выпуска, оглавление docs и обновлённые component README. В основном
быстром старте одна команда; подробности вынесены по задачам.

12 реальных скриншотов EN/RU, dark/light подготовлены в отдельной базе с
синтетическим эталоном, шестью настоящими дублями и примером очистки. Личные
профили/записи не использовались. Снимки занимают около 1,2 МБ. Проверены
198 относительных ссылок, 16 якорей, 44 браузерных состояния на 390/1280px
и 22 перехода между языками. Изображения просмотрены, временные состояния
загрузки пересняты. Основной текст обоих README: по 96 строк.

Сравнение подтвердило неизменность 2 проектов, 12 связей заданий и 155
пользовательских файлов. Набор трёх установленных моделей сохранён. Изменений
рабочего интерфейса/API нет; временные серверы и тестовые аудиоданные убраны
после проверки. Журналы: .runtime/maintenance/documentation-20261104T041632Z/.
