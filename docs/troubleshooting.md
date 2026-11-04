# Troubleshooting

**English** · [Русский](troubleshooting.ru.md) · [Home](../README.md)

## The page will not open

Start the app with the [launcher](setup.md), leave Terminal open, and use
`http://127.0.0.1:4173`. A browser tab does not start the backend. If setup failed,
resolve its Terminal error before reopening the page. A port conflict means
another application or studio is already using that address.

## “Permission denied” when launching

Unzip the project into a writable folder. If your archive tool removed executable
permissions, restore them once from the project folder:

```sh
chmod +x voice scripts/*.sh
```

Then run the normal launcher again. Do not run the app as root or with sudo.

## Setup or a model download failed

Check internet access and available disk space, then retry. The app verifies
downloaded files and retains resumable transfer data. If setup was interrupted,
rerun the launcher. If it explicitly reports an unfinished tool installation,
move only the named incomplete tool folder aside and rerun setup.

A TLS/certificate error needs a working network and valid certificates. Do not
disable verification or substitute untrusted weights. Some author servers can
be temporarily unavailable. Keep the full error and the model name.

## A model is downloaded but unavailable

Its dependencies or language resources may still be preparing. Wait for readiness,
or retry the installation if it failed. A weight file alone is not enough.
Confirm that the selected model supports the task and language you want.

## I cannot choose my saved voice

Cloned profiles are offered only for compatible cloning modes. Built-in and
described-voice modes use their own controls. F5 needs an English/Chinese reference.
If a profile was deleted, choose another one for new generations; old takes remain.

## Pronunciation, stress or English terms sound wrong

Use the model's speech-language setting, plain text and shorter scenes. Write
numbers and abbreviations as you want them spoken. Correct the reference transcript
and try a cleaner sample or another supported model. Silero offers explicit stress
and SSML; those tags are not universal. Always listen to important names and terms.

## The voice is flat, or an emotion tag is spoken

Check the [family-specific syntax](models.md#delivery-and-pauses). Prefer the
available delivery selector. Unsupported tags may be rejected, and supported
emotions do not guarantee a strong performance. The reference also affects delivery.

## Generation is slow or memory runs out

Models load for the first task; large CPU models can be slow. Jobs run one at a
time. Close other heavy applications or choose a smaller model. Piper is a small
Russian preset option. A download size is not a RAM requirement; see [measurements](model-resources.md).
An installed card does not mean its model is currently loaded in memory.

## Cleanup sounds unnatural or loses a word

Compare Before/After. Reduce voice restoration, then update the result. At full
noise removal this does not mix the noisy original back in. Clean generated speech
may need no enhancement. If the original is better, keep it; earlier versions remain.

## My microphone is unavailable or very quiet

Start recording explicitly and allow microphone access in the browser and macOS.
Check the selected input and the app's input meter. Keep a steady distance and avoid
clipping. Saving applies local leveling, but it cannot recover a badly recorded source.

## Edits or uploads disappeared after reload

Wait for server saving before closing. A selected local File may need to be chosen
again after reload; saved profiles, projects and completed results live on disk.
For a save conflict, load the server version or save your draft as a separate copy.
Do not clear browser storage while unsaved recovery drafts are still needed.

## Where are diagnostics?

Keep the Terminal error and relevant files from `.runtime/logs/`, especially
`model-downloads.log` and `python-worker.log`. Include the model, macOS version,
memory and steps to reproduce. Review logs before sharing: they can contain local
paths or text. Never attach your entire data folder or recordings by accident.

[Setup](setup.md) · [Models](models.md) · [Backups](storage.md)
