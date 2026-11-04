# Prototype Instructions

User selected Night Session (option 2) at `../design/concepts/02-night-session.png`.
Keep the dark graphite/brass studio, top navigation, scene list, editor, voice inspector
and timeline. Default to Russian and dark; support English and light/system themes.
Waveforms fill with the accent only up to actual audio playback time; unplayed audio
stays grey. Scene/take selection uses its border, never a fully accent-colored wave.
Pause preserves progress. Keep library, take and timeline progress synchronized.
Clicking a waveform seeks to that position, preserving playing/paused state. Timeline
seeking uses project time and keeps the remaining scene queue. Seeking must not toggle
playback, select another scene or navigate; scene labels remain separate selection buttons.
The scene list fills available panel height and scrolls only when its content exceeds it.
Render dropdowns outside scroll containers, anchor them to their trigger, flip/clamp within
the viewport, and keep outside-click, Escape and keyboard navigation working.
UI locale must never translate the script or change the speech-language setting.
Use project-local Hallmark and its local policy. Keep all assets local.
Java Spring Boot owns validated asynchronous jobs and durable metadata; its persistent Python
child owns offline MLX inference. Keep jobs serialized, report actual worker stages and errors,
and never fake successful generation or model downloads. Completed takes keep the exact source
text and actual seed. Editing a scene must not rewrite an existing recording. Keep demo clips
labelled separately. Preserve project drafts across reloads and unavailable backend states.
Only loopback endpoints are used. No cloud or clipboard access is needed. Microphone
capture in Cleanup starts only after an explicit Record click and browser permission.
The installed Fish MLX adapter fixes temperature at 0.8 and infers language from text; do not
pretend those controls configure the model. Seed, emotion tags and application pauses work.

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.

Voice creation lives in Voices: local upload, explicit name, excerpt selection, actual
Whisper progress, reference playback and editable exact transcript before atomic save.
A scene's voice selection persists and applies only to future takes. Existing takes retain
voice IDs and source text. Keep old CLI profiles compatible; never call this model training.

All in-page controls follow the studio design, including voice upload/review/catalog
players, dropdown option menus, ranges, disclosures and scrollbars. Use shared AudioPlayer,
SeekWave and Select components; never add browser-native audio controls. Keep keyboard
seeking, focus states, Escape/outside-click dismissal, real elapsed progress and both themes.

Keep responsive coverage from 320 to 1920 CSS pixels across every navigation view (including
Cleanup), both editor modes, RU/EN and both color modes. Upload selection uses the shared
FileUpload surface with one-file drop, replace/clear actions, filename wrapping and explicit
field errors. Never rely on opacity
alone to explain an unavailable action. Dropdowns must constrain their height to available
space above/below their trigger, rather than covering it in short windows. Menu triggers
inside any form must always be type="button". Preserve entered scripts and existing audio
while navigating or changing display settings; do not add decorative dashboards or filler.

Uploaded recordings use real waveforms, just like prepared references. Build waveform peaks
serially at a reduced analysis sample rate; leave the original playback/download data intact.
Show waveform loading and retry states instead of substituting a different-looking seek bar.
Pointer clicks must not leave focus outlines on waveforms, fields or buttons. Keyboard
navigation retains clear focus (a thin underline for a waveform). Keep meaningful selection
and validation borders. Volume stays visible beside each player: an inline fader with 1% steps, a percentage
readout and one-click mute. Never hide basic volume adjustment in a popup. Keep the
fader wide enough for direct adjustment and shared settings across local players.


Models is a real local catalog: use measured artifact sizes, actual required-file presence,
explicit downloads with byte progress, cancel/resume/retry, and durable installed selection.
Use a responsive tile grid with search and task/install filters, in the existing studio style.
Keep model tiles compact: one column on phones, two from760px, three from1120px and four
from1680px. Preserve the shared readable type scale, full descriptions and capabilities;
reduce empty spacing before shrinking text. Coarse-pointer actions stay at least44px tall.
Keep serving/runtime details inside disclosures or documentation. Never label the whole
application as demo; existing sample recordings keep honest sample labels. Decorative icons
are hidden from accessibility; named controls carry their own labels.

Keep the catalog broad across quality speech-synthesis families, preset voices, voice
design, dialogue, conversion and enhancement. Prioritize synthesis in the default order.
Research language/license/capabilities from model authors. Model files present on disk
do not imply a connected runtime: only ready integrations can become active. Keep
Russian, capability and runtime filters separate. Gated weights link to the author;
never accept license terms, read credentials or advertise an unavailable download.

Supported model installs prepare their hashed, isolated runtime automatically. Only models
with both verified weights and a current successful runtime probe are selectable. Freeze
model/preset/description with each job. Show only applicable voice, language and emotion
controls; never pass Fish tags to another family as spoken text. Keep cloning profiles
separate from preset/designed voices. Extra runtimes must not change the Fish environment.

Voices uses the full shared content width and a responsive tile grid, with name search,
6/12/24 items per page and a clamped page after filtering/deletion. Cards retain the shared
waveform player, visible volume, transcript and explicit use/delete actions. Deletion uses
a styled confirmation, is blocked for queued/running jobs, preserves generated recordings
and scene drafts, and leaves deleted voice selections unavailable until manually changed.

Before packaging a new Java jar, stop the idle managed API, then rebuild and restart it.
Do not leave the running API using a jar overwritten by Maven: lazy class loading breaks
reference playback. Check queued/running jobs before a restart.

Projects persist in the Java-owned SQLite database, with versioned migrations and CAS
revision checks. Preserve exact scripts, scene settings, take IDs and manual take selection.
Migrate legacy browser drafts idempotently; keep the original as a backup. Never show
“saved” before the server commits. Offline changes keep a per-tab local backup; human
conflicts need an explicit load-server or save-copy action. Reconcile completed jobs only
into their originating project, including jobs finished while the UI was closed.
A blank browser now loads existing server projects. Browser QA that edits projects MUST
route project endpoints to a separate temporary API/database; never modify the user's
current project or legacy localStorage. Preserve the active project ID across URL navigation.

Keep the app header visible while scrolling. The project timeline belongs only to Studio:
a compact fixed bottom dock with an exact measured content inset and collapse control.
Start collapsed on phones/short screens. Other tabs show no project timeline; an explicitly
started main recording may keep a compact dismissible player. Preserve playback/seek/queue
state across tab navigation. Do not obscure focused fields, menus or final page actions.

Voice-create form fields and the selected File survive tab navigation in the same session;
metadata can survive reload, but a File must be selected again after reload. Do not reset a
user-edited excerpt length when its audio player remounts. Header nav styles must be scoped
to .app-header nav so pagination keeps its own44px controls. Browser multipart QA uses a real
local proxy, not route.fetch interception, which can omit binary file bodies.

Use one compact app scale across views:14px UI,12px labels,16px script,18px section
heads,24px page heads,36-40px desktop controls and44px coarse-pointer targets. Never
increase studio text to20px just because the viewport is wide. From900px up, keep scene
list, editor and inspector side by side; primary settings and generation should fit a
standard1280x720/1366x768 viewport without page or inspector scrolling. Below900px use a
scene rail and collapsible settings. Fixed model-determined language is a compact readout,
not an unusable full-height dropdown. Keep user text/settings unchanged when resizing.

Montage is non-destructive and saved with the server project: per-source trim/gain edits,
scene exclusion/order/pause and shared mix options. Keep originals and exact take text intact.
The bottom project transport plays the rendered master, including cuts and gaps. Individual
source/take players keep their original audio; never silently skip included missing scenes.
Preview and export must use the same immutable render. Changing audio settings invalidates it;
text edits do not change existing takes. Remember scene selection and montage mode in the URL.
Keep default controls compact and maintain pointer/keyboard trim handles, reset and montage undo.
Keep trim boundaries on the waveform; do not show numeric start/end fields. Scene order
uses drag handles with pointer/touch dragging and keyboard pickup/drop, without arrow buttons.

Timeline clips keep timestamps, waveforms and caption/pause text in separate flow rows,
with visible inner padding and gaps. Never absolutely position time or pause labels over
waveforms or scene names. Preserve readable minimum clip widths and horizontal scrolling.

Montage actions need plain labels: explain scene gain versus listening volume, per-scene
pause versus default gap, and trim-at-cursor actions. Undo/redo buttons have visible names
and a real gap; do not pack ambiguous adjacent icon buttons into the scene heading.

Text and montage use exactly the same desktop columns and viewport-bound panel heights.
Scroll montage bodies inside aligned panels and keep final listen/download actions visible.
Group the text/montage toggle next to Export. Do not reintroduce trim-at-cursor buttons.
Scene gain uses a ticked slider plus optional numeric input; a pointer drag is one undo step.
Added silence occupies its proportional segment on the final timeline, with flat waveform,
its own seeking and moving playback position. Never stretch speech waves to disguise gaps.

Montage's selected-fragment player previews manual scene gain immediately, including during
slider drags and valid numeric drafts. Keep listening volume/mute downstream and independent.
A gain drag remains one persisted undo step. Original take downloads stay explicitly labelled
as original; final render still applies its own leveling, edge fades and limiter.

Audio cleanup has its own tab for standalone files; scene/final cleanup lives in the compact
header action menus. Keep the default editor uncluttered. Before/After uses the shared waveform
player and preserves cursor and playback state. Processing never auto-selects a take: explicit
Use in scene adds a new take and preserves its original source, draft text and per-source edits.
Final cleanup is a separate downloadable master, never an overwrite of scenes. Keep durable
history, real stages, cancellation/retry and unavailable-model states. Never imply cleanup
always improves clean synthesis. Originals, timing and inserted digital silence stay intact.

Cleanup's source and comparison panels have equal desktop widths and stretch to the same
height, with aligned headings/padding. On phones use natural content heights. Offer upload
and explicit microphone recording in the source panel, with pause, finish, cancel and a real
input level. Stop all microphone tracks on finish/cancel/navigation, including late permission
responses. Keep the old source until a replacement is saved successfully; cancellation and
permission errors preserve it. Navigating away finishes the capture into the local draft.
Recordings become finite-duration PCM WAVs for the shared player and existing cleanup API;
no automatic upload or cleanup. Limit browser recordings to5 minutes and explain the limit.

Audio enhancement uses one default automatic action and two independent controls: noise
removal and voice restoration. Full noise removal must NEVER mix the original noisy signal
back when voice restoration decreases. Default100% noise removal with30% restoration;
0% restoration keeps the natural denoised voice. Cache the denoised baseline and restoration
of that baseline separately; existing legacy versions keep their old output and settings. Put clarity,
voice warmth, sibilance reduction, leveling and peak protection inside Adjust the sound.
Freeze settings per submitted version; editing controls must clearly require Update result,
never pretend the saved waveform already reflects a draft. Reuse the immutable cached neural
restoration for later mastering, keeping source, old versions and scene trim/gain settings.
Reopening enhancement of an already enhanced scene should open that saved version, not
silently run restoration a second time on processed audio. Match Before/After loudness by
measured attenuation for audition only; downloads and scene application use the actual result.
Equal desktop panel widths/heights and natural phone heights remain required.

Microphone recording uses bounded local look-ahead leveling at save, including quiet opening
words, without a startup gain ramp or changing word timing. Preserve input buffers and cap
peaks; silence stays silent. Browser AGC remains off to avoid device-specific gain pumping.
Show a logarithmic measured input meter with quiet/normal/overload guidance, not a linear
RMS multiplier. Unlock its AudioContext during the explicit click, before awaiting permission;
release pending contexts as well as streams on cancellation, navigation or denied permission.
