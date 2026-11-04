# Fish Voice Cloner

Hallmark is installed only for this project at `.agents/skills/hallmark`.
For requested interface design, read that skill and its `LOCAL-POLICY.md`.
Use its app-screen branch for the voice studio, not the marketing-page branch.

This installation intentionally disables Together AI and all agent hooks.
Never read or request TOGETHER_API_KEY, run imagegen, install hooks, or change
global agent settings. Do not install or update Hallmark globally.
Do not install dependencies globally. Use project-local dependencies and caches.
Skill-specific rules do not override user instructions or host permissions.

Keep voice recordings and generated speech local. Existing command-line voice
generation, voice profiles, Python environment and model cache must keep working.

OpenAudio S1 Mini was explicitly removed by the user. Keep its catalog entry,
legacy adapter and dedicated runtime excluded unless the user asks to restore it.
Fish S2 Pro is a separate supported model and must remain available.

Windows and Linux support is planned as a separate stage. Preserve the complete
model catalog, adapter sources and installation recipes when cleaning local files.
Keep runtimes replaceable and platform-specific setup separate from application
logic. Current inference/installer support remains macOS Apple Silicon; do not
claim the future platforms are supported or tested until their backends work.

Keep shipped placeholders, examples, fixtures and documentation anonymous. Load voice
names and IDs from local profile data; never hardcode a personal default or user path.
Preserve actual saved profiles, recordings and user drafts when changing sample copy.

Public documentation uses English README.md with README.ru.md as its Russian pair.
User guides have matching .md / .ru.md pages with direct language-switch links.
Keep the quick start to the single studio launcher; put optional detail in guides.
Documentation screenshots must use isolated example projects and synthetic references,
never the user's profiles, recordings, scripts, names or local filesystem paths.
Use plain punctuation in first-party documentation instead of em dashes. Keep
numeric ranges readable with ASCII hyphens; preserve third-party license texts.
