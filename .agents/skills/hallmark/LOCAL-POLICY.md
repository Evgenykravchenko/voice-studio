# Project-local Hallmark policy

Installed for Fish Voice Cloner only. This policy takes precedence over the
upstream Hallmark flow where they differ.

- Source: https://github.com/Nutlope/hallmark
- Upstream version: 2.0.0
- Pinned commit: 8f6969f8922caabde9de1784959eae11ddf68073
- Path: skills/hallmark
- License: MIT; original LICENSE retained.

## Disabled integrations

Together AI is disabled even if TOGETHER_API_KEY exists in the environment.
Do not inspect the key, load the comp workflow, make Together requests, ask for
credentials, or generate assets via Together. `scripts/imagegen.mjs` is a
no-network stub that exits with status 2.

Hooks are disabled. `scripts/install-hook.mjs` exits with status 2 without reading
or changing settings. `scripts/lint-hook.mjs` is inert. No hooks are registered.
The global installer `scripts/install.mjs` is also disabled. Never invoke it as
an update mechanism; updates require preserving and reviewing these local changes.

## Retained capabilities

Design guidance, themes, app-screen rules, manually invoked static linting and
optional explicitly scoped browser verification remain available. Browser checks
require local Puppeteer and Chrome; those dependencies are not installed by this
skill installation. Use existing host browser tools when appropriate and permitted.
Do not install npm packages globally or weaken tool approval policies.

External fonts/photos are a separate upstream feature, not part of Together.
For the self-hosted voice studio prefer local assets and fonts supporting Cyrillic;
do not silently add third-party requests to the product.

This is a locally modified copy, not an unmodified upstream release. No automatic
updates or background services are installed. It is available only to agent tasks
whose project scope includes the Fish Voice Cloner directory.
