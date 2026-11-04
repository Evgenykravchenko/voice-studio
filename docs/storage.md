# Your data and updates

**English** · [Русский](storage.ru.md) · [Home](../README.md)

## What is saved

Projects save automatically. Wait for **Saved on server** before closing. A fresh
browser can load saved projects from the local backend; browser storage is only
an additional recovery draft, plus your language and appearance preferences.

| Location | Contents |
| --- | --- |
| `data/` | Project database, voice references, job settings, imported sources and processing history. |
| `outputs/` | Generated speech, assembled mixes and processed audio. |
| `.runtime/` | Local tools, model weights, optional runtimes, caches and logs. |
| `.venv/` | The main Python environment. |

These local folders are excluded from Git. An optional legacy sample folder
`frontend/public/audio/` and its `frontend/src/audio-data.json` manifest are private too.

Project JSON export contains the script, settings and recording IDs. **It does
not include WAV files or voice references.** Keep the underlying data for a full restore.

## Back up

1. Wait for saves to finish, stop active tasks, then stop the studio with Ctrl+C.
2. Copy **all of `data/` and `outputs/`** to a separate location.
3. If you use legacy local samples, also copy their folder and manifest listed above.

Copying the whole stopped project is also valid, but includes large caches.
Model weights can be downloaded again; personal recordings cannot be recreated
from project JSON. Never copy just the main SQLite file while the app is writing:
its current state can also be in WAL files.

## Update

Stop the studio and make a backup first. Update the source with your Git client,
then run this once from the project folder:

```sh
./scripts/bootstrap.sh
```

Start normally with the launcher. Bootstrap updates local dependencies and the
app build; it does not delete your data. It refuses to update a running studio.

If you downloaded ZIP instead, extract the new version into a separate folder,
copy your backed-up data and outputs into it, and launch there. Install the models
you need in the new copy. Keep the old folder until the new copy opens your work.

## Move or remove

To move an existing installation on a compatible Mac, stop it and move the whole
project folder. The launcher checks local Python locations and can repair them
through setup. Moving to a different operating system is not supported yet.

To uninstall, stop the app, move your backups outside its folder, then remove the
project folder. There is no system-wide Python/Java installation to uninstall.

The catalog currently has no individual model-uninstall button. Avoid deleting
shared Hugging Face blob files manually. If you intentionally clear the **whole**
model cache while the app is stopped, models will need to be installed again;
keep `data/` and `outputs/`. Starting with only the models you need saves space.

[Troubleshooting](troubleshooting.md) · [Publication notes](publication.md)
