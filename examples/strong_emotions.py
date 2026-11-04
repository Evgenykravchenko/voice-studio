"""Separate takes for a more contrasting Fish S2 Pro emotion demonstration."""

import argparse
import json
from pathlib import Path

from voice_cloner.cli import _ensure_local_environment, _load_profile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--profile", required=True, help="ID of an existing local voice profile")
args = parser.parse_args()

_ensure_local_environment()
profile, reference = _load_profile(args.profile)

import mlx.core as mx
import mlx_speech
import numpy as np
from mlx_speech.audio import write_wav

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "strong-emotions" / args.profile
OUT.mkdir(parents=True, exist_ok=True)
TAKES = [
    ("01-neutral", "Спокойно", "[neutral] Я только что узнал эту новость. Сейчас расскажу тебе всё по порядку."),
    ("02-joy", "Восторг", "[extremely excited, ecstatic, bursting with joy] Наконец получилось! [excited] Да! Мы победили! Я просто не могу поверить! Это невероятно!"),
    ("03-sad", "Грусть", "[deeply sad, tearful, voice trembling with grief] Я так надеялся, что ты останешься. [sigh] Но теперь тебя здесь нет. Мне очень тебя не хватает."),
    ("04-angry", "Гнев", "[angry] Ты опять всё удалил?! [shouting] Я же просил ничего не трогать! [angry] Хватит! Немедленно остановись!"),
    ("05-whisper", "Шёпот", "[whisper] Тише. Никому об этом не говори. [whisper in a very quiet breathy voice] Подойди поближе. Я расскажу тебе один маленький секрет."),
    ("06-laugh", "Смех", "[laughing] Не могу! [laughing] Я полчаса искал очки, а они всё это время были у меня на голове! [chuckle] Вот это я молодец!"),
]

print("Loading Fish S2 Pro…", flush=True)
model = mlx_speech.tts.load("fish-s2-pro")
voice = model.prepare_reference(str(reference), reference_text=profile["reference_text"])
parts = []
timeline = []
elapsed = 0.0
sample_rate = 44100
for index, (name, label, text) in enumerate(TAKES):
    print(f"{index + 1}/{len(TAKES)}: {label}", flush=True)
    mx.random.seed(1500 + index)
    result = model.generate(text, reference_audio=voice, max_new_tokens=600)
    sample_rate = result.sample_rate
    samples = np.asarray(result.waveform, dtype=np.float32).reshape(-1)
    if not np.isfinite(samples).all() or samples.size == 0:
        raise RuntimeError(f"Invalid audio: {name}")
    write_wav(str(OUT / f"{name}.wav"), result.waveform, sample_rate=sample_rate)
    duration = len(samples) / sample_rate
    rms = float(np.sqrt(np.mean(samples * samples)))
    timeline.append({"label": label, "start": round(elapsed, 2), "duration": round(duration, 2), "rms_dbfs": round(20 * np.log10(max(rms, 1e-10)), 2), "text": text})
    parts.extend([samples, np.zeros(int(0.9 * sample_rate), dtype=np.float32)])
    elapsed += duration + 0.9
    print(f"  {duration:.1f} sec", flush=True)
    mx.clear_cache()

combined = np.concatenate(parts[:-1])
write_wav(str(ROOT / "outputs" / f"{args.profile}-emotions-strong.wav"), mx.array(combined), sample_rate=sample_rate)
(OUT / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(timeline, ensure_ascii=False, indent=2), flush=True)
print(f"Total: {len(combined) / sample_rate:.1f} sec", flush=True)
