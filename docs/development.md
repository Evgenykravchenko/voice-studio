# Development and CLI

**English** · [Русский](development.ru.md) · [Home](../README.md)

## Structure

| Part | Responsibility |
| --- | --- |
| `frontend/` | React, TypeScript and Vite; the browser interface. |
| `server/` | Java 21 and Spring Boot; local API, validation, queues and durable metadata. |
| `src/voice_cloner/` | Python inference, audio processing, catalog and runtime management. |
| `engines/` | Dependency locks, source recipes and reviewed native wheels. |
| `vendor/` | Third-party inference sources and their licenses. |

Normal mode serves the built frontend and API together on 4173. Node builds the
interface; it is not another production service. Python starts lazily and runs
one task at a time. SQLite is embedded: PostgreSQL and Redis are not required.

Windows/Linux are future work. The interface and Java API are separate from
inference, but current MLX backends and setup target Apple Silicon. Other platforms
need suitable backends, platform-specific installation and testing.

## Work locally

Complete [normal setup](setup.md) first. Stop normal mode, then start development:

```sh
./scripts/studio.sh --dev
```

Vite runs on 4173 and Java on 7080. Dependencies stay project-local. Do not
overwrite a running JAR; the packaging script checks for this.

Run relevant checks from the project root:

```sh
./.venv/bin/python -m unittest discover -s tests
./scripts/server.sh test
./.runtime/toolchains/node/bin/node --test frontend/tests/*.test.mjs
```

Packaging tests expect the frontend build produced by setup. Build the Java JAR
with `./scripts/server.sh build` while the studio is stopped. Use local Node/pnpm
for frontend scripts; see [frontend notes](../frontend/README.md).
Real inference scripts under `scripts/verify-*.py` can use substantial memory,
disk and time. Use separate test data, not personal projects.

## Optional CLI

The interface is sufficient for normal use. The CLI uses Fish; choosing another
web model does not change its backend.

```sh
./voice doctor
./voice profile list
./voice generate --help
```

App profiles also appear in the CLI list. Use an actual ID from that list.
To prepare a separate profile from a file:

```sh
./voice profile create narrator --audio sample.wav --duration 20
./voice generate --profile narrator --text "Welcome to the studio."
```

Review the sample transcript. Keep CLI inference and studio model tasks separate
to avoid competing workloads.

[Runtime details](../engines/README.md) · [Backend API](../server/README.md)
· [Publishing source](publication.md)
