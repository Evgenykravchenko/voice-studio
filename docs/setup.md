# Setup

**English** · [Русский](setup.ru.md) · [Home](../README.md)

## Before you start

| Requirement | What you need |
| --- | --- |
| Computer | A Mac with Apple Silicon: M1 or newer. Intel Macs are not supported. |
| System | macOS 14 or newer. Windows and Linux are planned. |
| Internet | For initial setup, model downloads and updates. |
| Storage | Room for the app, tools, selected models and download caches. |
| Memory | Depends on the model; see [memory notes](models.md#memory-and-storage). |

The launcher installs project-local Java, Python, Node.js, pnpm, Maven and uv.
FFmpeg comes with the Python dependencies. No Homebrew or global package
installation is required. Keep the project in a normal, writable folder.

## Install and launch

1. Download **Code → Download ZIP** and unzip it, or use your Git client.
2. Open the extracted project folder in Terminal.
3. Run:

```sh
./scripts/studio.sh
```

On a fresh checkout the launcher performs setup automatically. Wait for it to
finish, then open [http://127.0.0.1:4173](http://127.0.0.1:4173).
Some installer messages are currently in Russian. Keep the full error if setup fails.

The first launch installs the application, **not every model**. Open Models and install:

- **Fish S2 Pro + Whisper Small** for cloning and speech generation.
- **A Piper voice** for ready-made Russian speech without a reference recording.
- **Resemble Enhance** for audio cleanup without a cloning profile.

A model becomes usable after file verification and dependency preparation finish.
Some downloads are large; let setup continue on a slow connection.
[Choose a model →](models.md)

## Start again and stop

Use the same launcher for later sessions. It reuses installed tools and data.
Keep its Terminal window open while working. Press **Ctrl+C** there to stop.
Closing a browser tab alone does not stop the backend.

An existing matching studio is reused. If another application owns port 4173,
the launcher reports the conflict. Stopping interrupts unfinished jobs;
saved projects and completed results remain.

Fish releases its model after 180 idle seconds. Other models run in isolated
children that exit after the task. A small idle Python process can remain while
the backend runs. There is no continuous microphone listening.

[Create your first voice](guide.md) · [Troubleshooting](troubleshooting.md) · [Update or move](storage.md)
