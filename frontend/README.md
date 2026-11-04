# Voice Studio · frontend

**English** · [Русский](README.ru.md) · [User documentation](../README.md)

React, TypeScript and Vite. The interface has six views: Speech, Projects, Voices,
Models, Library and Audio enhancement. It uses the local Java API for durable
projects, profiles, downloads and model tasks. Normal operation serves this build
through Java on 4173; development uses Vite on 4173 with an API proxy to 7080.

Start the full application with the root launcher. See [development](../docs/development.md)
for the development launcher and checks. Project-local Node/pnpm are installed
by bootstrap; global packages are not required.

## Build and tests

`package.json` defines `typecheck`, `build`, `test:menu` and `test:sites`.
The build runs TypeScript, Vite and `scripts/prepare-sites-build.mjs`. It produces
`dist/client/index.html`, the optional static-hosting worker and hosting metadata.
The worker serves assets; it does not replace the Java/Python inference backend.

Run all frontend checks from the project root:

```sh
./.runtime/toolchains/node/bin/node --test frontend/tests/*.test.mjs
```

Packaging checks expect an existing frontend build. Stop the app before rebuilding
the served output. Personal audio in `public/audio/` is excluded from the build.
`src/audio-data.json` is optional local sample metadata, excluded from Git.

## Interface conventions

Use shared Select, FileUpload, AudioPlayer and waveform components. Keep RU/EN,
light/dark/system modes, keyboard controls and responsive layouts. Browser
language does not translate a script or change its speech language. Screenshot
or integration tests must use an isolated API/database and anonymous files.

[Studio guide](../docs/guide.md) · [Data and backups](../docs/storage.md)
