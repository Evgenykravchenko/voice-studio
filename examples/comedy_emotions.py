"""A comic Fish S2 Pro skit, with raw and loudness-contrasted exports."""

import argparse
import json
from pathlib import Path

from voice_cloner.cli import _ensure_local_environment, _load_profile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--profile", required=True, help="ID of an existing local voice profile")
parser.add_argument("--redo", help="Reuse existing raw clips except this scene ID")
args = parser.parse_args()

_ensure_local_environment()
profile, reference = _load_profile(args.profile)

import mlx.core as mx
import mlx_speech
import numpy as np
import soundfile as sf
from mlx_speech.audio import write_wav

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "comedy-emotions" / args.profile
OUT.mkdir(parents=True, exist_ok=True)

# Last field is the mix target in dBFS. Pitch and speed remain unmodified.
SCENES = [
    ("01-news", "Диктор", "[deadpan, serious professional newsreader] Срочные новости. В два часа ночи один человек объявил холодильнику внеплановую проверку. Цель операции: пельмени.", -21),
    ("02-whisper", "Тайный шёпот", "[whisper in a tiny breathy voice] Тихо. Все спят. [whisper] Открываем морозилку. Если заскрипит пакет, говорим, что это кот. Кота у нас нет, но сейчас это неважно.", -28),
    ("03-joy", "Безумный восторг", "[excited] Ура! Пельмени! [shouting] Мама! Я нашёл своё призвание! [excited] Я богат! Я успешен! Несите сметану!", -17),
    ("04-panic", "Паника", "[terrified, gasping, panicked] Стой! Что это?! [screaming] Это не пельмени! Это замороженная цветная капуста! [panicked] Почему она смотрит на меня?!", -17),
    ("05-grief", "Трагедия", "[sobbing, devastated, crying, voice breaking with grief] Пельмешки. Родные мои. [sigh] Мы ведь столько пережили вместе. Хотя нет. Это были другие пельмешки. Но всё равно больно.", -24),
    ("06-rage", "Ярость", "[furious, shouting angrily] Кто положил капусту в пакет от пельменей?! [shouting] Это кулинарное предательство! [angry] Я требую адвоката! И хотя бы сосиску!", -16),
    ("07-laugh", "Злодейский смех", "[laughing uncontrollably] Подождите! Настоящие пельмени лежали в соседнем ящике! [laughing] А я уже с брокколи попрощался! [evil laugh] Всё! Пельменная империя наносит ответный ужин!", -18),
]

print("Loading Fish S2 Pro…", flush=True)
model = mlx_speech.tts.load("fish-s2-pro")
voice = model.prepare_reference(str(reference), reference_text=profile["reference_text"])
raw_parts, mixed_parts, timeline = [], [], []
elapsed = 0.0
sample_rate = 44100
for index, (name, label, text, target_dbfs) in enumerate(SCENES):
    print(f"{index + 1}/{len(SCENES)}: {label}", flush=True)
    raw_path = OUT / f"{name}-raw.wav"
    if args.redo and name != args.redo and raw_path.exists():
        samples, sample_rate = sf.read(raw_path, dtype="float32")
    else:
        mx.random.seed(2500 + index)
        result = model.generate(text, reference_audio=voice, max_new_tokens=700)
        sample_rate = result.sample_rate
        samples = np.asarray(result.waveform, dtype=np.float32).reshape(-1)
    if not samples.size or not np.isfinite(samples).all():
        raise RuntimeError(f"Invalid audio: {name}")
    duration = samples.size / sample_rate
    rms = float(np.sqrt(np.mean(samples * samples)))
    source_dbfs = 20 * np.log10(max(rms, 1e-10))
    peak = float(np.max(np.abs(samples)))
    gain = min(10 ** ((target_dbfs - source_dbfs) / 20), 0.97 / max(peak, 1e-10))
    mixed = samples * gain
    write_wav(str(OUT / f"{name}-raw.wav"), mx.array(samples), sample_rate=sample_rate)
    write_wav(str(OUT / f"{name}.wav"), mx.array(mixed), sample_rate=sample_rate)
    gap = np.zeros(round(0.65 * sample_rate), dtype=np.float32)
    raw_parts.extend([samples, gap])
    mixed_parts.extend([mixed, gap])
    timeline.append({"label": label, "start": round(elapsed, 2), "duration": round(duration, 2), "text": text, "mix_gain_db": round(20 * np.log10(gain), 2)})
    elapsed += duration + 0.65
    print(f"  {duration:.1f} sec; mix gain {20 * np.log10(gain):+.1f} dB", flush=True)
    mx.clear_cache()

for suffix, parts in [("raw", raw_parts), ("mix", mixed_parts)]:
    combined = np.concatenate(parts[:-1])
    write_wav(str(ROOT / "outputs" / f"{args.profile}-comedy-{suffix}.wav"), mx.array(combined), sample_rate=sample_rate)
(OUT / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(timeline, ensure_ascii=False, indent=2), flush=True)
print(f"Total: {len(combined) / sample_rate:.1f} sec", flush=True)
