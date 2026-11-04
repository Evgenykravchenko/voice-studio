from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
PROFILES_DIR = PROJECT_DIR / "data" / "profiles"
OUTPUTS_DIR = PROJECT_DIR / "outputs"
MODEL_NAME = "fish-s2-pro"
WHISPER_MODEL = "mlx-community/whisper-small-mlx-q4"
PROFILE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def _ensure_local_environment() -> None:
    runtime = PROJECT_DIR / ".runtime"
    runtime_bin = runtime / "bin"
    runtime_bin.mkdir(parents=True, exist_ok=True)
    env_defaults = {
        "XDG_CACHE_HOME": runtime / "cache",
        "HF_HOME": runtime / "cache" / "huggingface",
        "HUGGINGFACE_HUB_CACHE": runtime / "cache" / "huggingface" / "hub",
        "TORCH_HOME": runtime / "cache" / "torch",
        "MPLCONFIGDIR": runtime / "cache" / "matplotlib",
        "PYTHONPYCACHEPREFIX": runtime / "pycache",
    }
    for key, value in env_defaults.items():
        os.environ.setdefault(key, str(value))
        Path(value).mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")
    ffmpeg_link = runtime_bin / "ffmpeg"
    if not ffmpeg_link.is_file() or ffmpeg_link.is_symlink():
        import imageio_ffmpeg
        executable=Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
        target=os.path.relpath(executable,runtime_bin.resolve())
        # A copied installation can retain an absolute link to its old venv,
        # including a dangling link. Replace it atomically with a relative one.
        if not ffmpeg_link.is_symlink() or os.readlink(ffmpeg_link)!=target:
            temporary=runtime_bin/f'.ffmpeg-{os.getpid()}'
            try:
                temporary.symlink_to(target)
                temporary.replace(ffmpeg_link)
            finally:temporary.unlink(missing_ok=True)
    os.environ["PATH"] = f"{runtime_bin}{os.pathsep}{os.environ.get('PATH', '')}"
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def _profile_dir(profile_id: str) -> Path:
    if not PROFILE_ID_PATTERN.fullmatch(profile_id):
        raise ValueError("ID профиля: только латиница, цифры, дефис и подчёркивание")
    return PROFILES_DIR / profile_id


def _load_profile(profile_id: str) -> tuple[dict, Path]:
    directory = _profile_dir(profile_id)
    metadata_path = directory / "profile.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Профиль '{profile_id}' не найден. Посмотрите: ./voice profile list")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    reference = directory / metadata["reference_audio"]
    if not reference.exists():
        raise FileNotFoundError(f"Нет эталонного аудио профиля: {reference}")
    return metadata, reference


def _ffmpeg_executable() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError(f"Не удалось найти изолированный ffmpeg: {exc}") from exc


def _prepare_audio(source: Path, destination: Path, start: float, duration: float) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Аудиофайл не найден: {source}")
    if start < 0 or duration <= 0 or duration > 30:
        raise ValueError("Начало должно быть >= 0, длительность — от 1 до 30 секунд")
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        _ffmpeg_executable(),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        str(start),
        "-i",
        str(source),
        "-t",
        str(duration),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "44100",
        "-c:a",
        "pcm_s16le",
        str(destination),
    ]
    subprocess.run(command, check=True)


def _transcribe(reference: Path) -> str:
    print("Расшифровываю эталон локально с Whisper Small…")
    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(reference),
        path_or_hf_repo=WHISPER_MODEL,
        language="ru",
        verbose=None,
    )
    text = str(result.get("text", "")).strip()
    if not text:
        raise RuntimeError("Whisper не обнаружил речь. Выберите другой фрагмент аудио")
    return text


def cmd_doctor(_: argparse.Namespace) -> None:
    import platform

    print(f"Проект:       {PROJECT_DIR}")
    print(f"Python:       {platform.python_version()} ({sys.executable})")
    print(f"Архитектура:  {platform.machine()}")
    print(f"Кеш моделей:  {os.environ['HF_HOME']}")
    print(f"Профили:      {PROFILES_DIR}")
    print(f"Результаты:   {OUTPUTS_DIR}")
    print(f"ffmpeg:       {_ffmpeg_executable()}")


def cmd_model_download(_: argparse.Namespace) -> None:
    from .models import download

    print("Скачиваю Fish S2 Pro INT8 в кеш проекта…", flush=True)
    download('fish-s2-pro')
    print("Скачиваю Whisper Small Q4…", flush=True)
    download('whisper-small')
    print("Fish S2 Pro и Whisper скачаны. Модели можно выбрать в студии.")


def cmd_profile_create(args: argparse.Namespace) -> None:
    directory = _profile_dir(args.profile_id)
    if directory.exists() and not args.replace:
        raise FileExistsError(
            f"Профиль '{args.profile_id}' уже существует. Для замены добавьте --replace"
        )
    directory.mkdir(parents=True, exist_ok=True)
    reference = directory / "reference.wav"
    source = Path(args.audio).expanduser().resolve()
    _prepare_audio(source, reference, args.start, args.duration)

    transcript = (args.transcript or "").strip()
    if args.transcript_file:
        transcript = Path(args.transcript_file).expanduser().read_text(encoding="utf-8").strip()
    if not transcript:
        transcript = _transcribe(reference)

    metadata = {
        "id": args.profile_id,
        "name": args.name or args.profile_id,
        "engine": MODEL_NAME,
        "language": "ru",
        "reference_audio": reference.name,
        "reference_text": transcript,
        "source_audio": str(source),
        "clip_start_seconds": args.start,
        "clip_duration_seconds": args.duration,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (directory / "profile.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Профиль создан: {args.profile_id} ({metadata['name']})")
    print(f"Расшифровка: {transcript}")
    print("Совет: прослушайте data/profiles/<ID>/reference.wav и проверьте расшифровку.")


def cmd_profile_list(_: argparse.Namespace) -> None:
    found = False
    for metadata_path in sorted(PROFILES_DIR.glob("*/profile.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        print(f"{metadata['id']}: {metadata['name']}")
        found = True
    if not found:
        print("Профилей пока нет.")


def cmd_profile_show(args: argparse.Namespace) -> None:
    metadata, reference = _load_profile(args.profile_id)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(f"reference_path: {reference}")


def _read_generation_text(args: argparse.Namespace) -> str:
    if args.text_file:
        return Path(args.text_file).expanduser().read_text(encoding="utf-8").strip()
    return (args.text or "").strip()


def cmd_generate(args: argparse.Namespace) -> None:
    text = _read_generation_text(args)
    if not text:
        raise ValueError("Передайте --text или --text-file")
    metadata, reference = _load_profile(args.profile)
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else OUTPUTS_DIR / f"{args.profile}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.wav"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Загружаю {MODEL_NAME} и профиль '{metadata['name']}'…")
    import mlx_speech
    from mlx_speech.audio import write_wav

    model = mlx_speech.tts.load(MODEL_NAME)
    voice = model.prepare_reference(
        str(reference),
        reference_text=metadata["reference_text"],
    )
    print("Создаю озвучку…")
    result = model.generate(
        text,
        reference_audio=voice,
        max_new_tokens=args.max_new_tokens,
    )
    write_wav(str(output), result.waveform, sample_rate=result.sample_rate)
    print(f"Готово: {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voice",
        description="Локальное клонирование голоса через Fish Audio S2 Pro MLX",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Проверить изолированное окружение")
    doctor.set_defaults(func=cmd_doctor)

    model = subparsers.add_parser("model", help="Управление моделью")
    model_sub = model.add_subparsers(dest="model_command", required=True)
    download = model_sub.add_parser("download", help="Скачать модель в проект")
    download.set_defaults(func=cmd_model_download)

    profile = subparsers.add_parser("profile", help="Голосовые профили")
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)

    create = profile_sub.add_parser("create", help="Создать профиль из аудио")
    create.add_argument("profile_id", help="Короткий ID, например my-voice")
    create.add_argument("--name", help="Отображаемое имя")
    create.add_argument("--audio", required=True, help="Путь к MP3/WAV/M4A")
    create.add_argument("--transcript", help="Точная расшифровка выбранного фрагмента")
    create.add_argument("--transcript-file", help="UTF-8 файл с расшифровкой")
    create.add_argument("--start", type=float, default=0.0, help="Начало фрагмента, секунды")
    create.add_argument(
        "--duration", type=float, default=20.0, help="Длительность фрагмента, максимум 30 секунд"
    )
    create.add_argument("--replace", action="store_true", help="Заменить существующий профиль")
    create.set_defaults(func=cmd_profile_create)

    list_profiles = profile_sub.add_parser("list", help="Показать профили")
    list_profiles.set_defaults(func=cmd_profile_list)
    show = profile_sub.add_parser("show", help="Показать профиль")
    show.add_argument("profile_id")
    show.set_defaults(func=cmd_profile_show)

    generate = subparsers.add_parser("generate", help="Озвучить текст выбранным профилем")
    generate.add_argument("--profile", required=True, help="ID голосового профиля")
    text_group = generate.add_mutually_exclusive_group(required=True)
    text_group.add_argument("--text", help="Текст или текст с [эмоциональной разметкой]")
    text_group.add_argument("--text-file", help="UTF-8 файл с текстом")
    generate.add_argument("--output", help="Путь для WAV")
    generate.add_argument("--max-new-tokens", type=int, default=2048)
    generate.set_defaults(func=cmd_generate)
    return parser


def main() -> None:
    _ensure_local_environment()
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("Отменено.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

