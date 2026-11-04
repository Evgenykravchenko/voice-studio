# Voice Studio · backend

**English** · [Русский](README.ru.md) · [User documentation](../README.md)

Java 21 and Spring Boot. Normal mode serves the API and built frontend on
`127.0.0.1:4173`; development uses the API on 7080 behind Vite. Run the full
app with the root launcher. [Development and checks →](../docs/development.md)

## Responsibilities

The server validates requests, serializes inference work, manages model downloads,
and persists projects and task metadata. SQLite is embedded. A Python worker starts
on demand, and optional runtimes run isolated inference children. The API binds
to loopback and is intended for one local user, not public internet hosting.

## API map

| Path | Purpose |
| --- | --- |
| `/api/health` | API capabilities, worker presence and project identity. “Ready” does not mean a model is resident. |
| `/api/models` | Inventory, readiness and selected models; subroutes download, cancel and select. |
| `/api/projects` | Create/list projects; ID routes load and save with revision checks. |
| `/api/voices`, `/api/voice-imports` | Profiles and asynchronous sample preparation/review/save. |
| `/api/jobs`, `/api/recordings` | Submit speech, inspect jobs and page through recording history. |
| `/api/audio/{id}` | Completed audio with range support for seeking. |
| `/api/projects/{id}/assembly` | Render a mix from a saved project. |
| `/api/cleanups` | Upload, process, compare, tune and apply enhancement results. |
| `/api/media` | Upload source media for model tools. |

Request schemas and exact verbs are defined in the API classes under
[`src/main/java/local/voicestudio`](src/main/java/local/voicestudio).
Jobs preserve their source settings. Interrupted jobs become failed on restart;
completed results remain. Do not package over a running JAR.

## Data

The database is `data/studio/studio.db`; metadata lives under `data/studio/`,
profiles under `data/profiles/`, and audio under `outputs/`. Follow the
[backup guide](../docs/storage.md) rather than copying a live SQLite file alone.
Python diagnostics and download logs are in `.runtime/logs/`.

[Runtime details](../engines/README.md) · [Model catalog](../docs/models.md)
