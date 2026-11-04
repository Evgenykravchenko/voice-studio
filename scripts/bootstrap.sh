#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) ;;
  *) echo 'Этот выпуск поддерживает macOS на Apple Silicon. Другие платформы пока не проверены.' >&2; exit 1 ;;
esac
STUDIO_MACOS_MAJOR=$(sw_vers -productVersion | cut -d . -f 1)
if [ "$STUDIO_MACOS_MAJOR" -lt 14 ]; then
  echo 'Для этого выпуска нужна macOS14 или новее.' >&2; exit 1
fi
STUDIO_PYTHON_ONLY=0
case "${1:-}" in
  '') ;;
  --python-only) STUDIO_PYTHON_ONLY=1 ;;
  *) echo 'Использование: ./scripts/bootstrap.sh [--python-only]' >&2; exit 2 ;;
esac
# Refuse an update before changing dependencies or replacing the running JAR.
if [ -x .venv/bin/python ]; then
  for STUDIO_RUNNING_PORT in 4173 7080; do
    if .venv/bin/python scripts/check-studio.py --port "$STUDIO_RUNNING_PORT" --root "$PROJECT_ROOT"; then
      echo 'Студия этого проекта запущена. Остановите её перед обновлением.' >&2; exit 1
    fi
  done
fi
. ./scripts/toolchain-pins.sh
. ./scripts/runtime-env.sh
mkdir -p .runtime/bin .runtime/cache/toolchains .runtime/toolchains data/profiles outputs
STUDIO_SETUP_LOCK="$PROJECT_ROOT/.runtime/setup.lock"
if ! mkdir "$STUDIO_SETUP_LOCK" 2>/dev/null; then
  STUDIO_SETUP_PID=$(cat "$STUDIO_SETUP_LOCK/pid" 2>/dev/null || true)
  if [ -n "$STUDIO_SETUP_PID" ] && kill -0 "$STUDIO_SETUP_PID" 2>/dev/null; then
    echo 'Установка уже выполняется. Дождитесь её завершения.' >&2; exit 1
  fi
  rm -f "$STUDIO_SETUP_LOCK/pid"
  rmdir "$STUDIO_SETUP_LOCK" && mkdir "$STUDIO_SETUP_LOCK"
fi
printf '%s\n' "$$" > "$STUDIO_SETUP_LOCK/pid"
STUDIO_UNPACK=
cleanup_setup() {
  [ -z "$STUDIO_UNPACK" ] || rm -rf "$STUDIO_UNPACK"
  if [ "$(cat "$STUDIO_SETUP_LOCK/pid" 2>/dev/null || true)" = "$$" ]; then
    rm -f "$STUDIO_SETUP_LOCK/pid"; rmdir "$STUDIO_SETUP_LOCK"
  fi
}
trap cleanup_setup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
install_archive() {
  STUDIO_TOOL=$1; STUDIO_VERSION=$2; STUDIO_URL=$3; STUDIO_HASH_ALGORITHM=$4; STUDIO_HASH=$5
  STUDIO_DEST="$PROJECT_ROOT/.runtime/toolchains/$STUDIO_TOOL-$STUDIO_VERSION"
  if [ ! -f "$STUDIO_DEST/.verified" ] || [ "$(cat "$STUDIO_DEST/.verified" 2>/dev/null || true)" != "$STUDIO_HASH" ]; then
    STUDIO_ARCHIVE="$PROJECT_ROOT/.runtime/cache/toolchains/$STUDIO_TOOL-$STUDIO_VERSION.tar.gz"
    if [ ! -f "$STUDIO_ARCHIVE" ] || [ "$(shasum -a "$STUDIO_HASH_ALGORITHM" "$STUDIO_ARCHIVE" | cut -d ' ' -f 1)" != "$STUDIO_HASH" ]; then
      printf 'Скачиваем %s %s…\n' "$STUDIO_TOOL" "$STUDIO_VERSION"
      curl --silent --show-error --proto '=https' --tlsv1.2 --fail --location --retry 3 --retry-all-errors --connect-timeout 20 --max-time 7200 --continue-at - --output "$STUDIO_ARCHIVE.part" "$STUDIO_URL"
      if [ "$(shasum -a "$STUDIO_HASH_ALGORITHM" "$STUDIO_ARCHIVE.part" | cut -d ' ' -f 1)" != "$STUDIO_HASH" ]; then
        rm -f "$STUDIO_ARCHIVE.part"; echo "Контрольная сумма $STUDIO_TOOL не совпала. Повторите установку." >&2; exit 1
      fi
      mv "$STUDIO_ARCHIVE.part" "$STUDIO_ARCHIVE"
    fi
    STUDIO_UNPACK="$PROJECT_ROOT/.runtime/toolchains/.unpack-$STUDIO_TOOL-$$"
    mkdir "$STUDIO_UNPACK"
    tar -xzf "$STUDIO_ARCHIVE" --strip-components=1 -C "$STUDIO_UNPACK"
    printf '%s\n' "$STUDIO_HASH" > "$STUDIO_UNPACK/.verified"
    if [ -e "$STUDIO_DEST" ]; then echo "Незавершённая установка $STUDIO_DEST. Сохраните её отдельно и повторите." >&2; exit 1; fi
    mv "$STUDIO_UNPACK" "$STUDIO_DEST"; STUDIO_UNPACK=
  fi
  ln -sfn "$STUDIO_TOOL-$STUDIO_VERSION" "$PROJECT_ROOT/.runtime/toolchains/$STUDIO_TOOL"
}
install_archive uv "$STUDIO_UV_VERSION" "$STUDIO_UV_URL" 256 "$STUDIO_UV_SHA256"
# Leave an already-running installer executable intact when it is the same version.
if [ ! -x .runtime/bin/uv ] || [ "$(.runtime/bin/uv --version | cut -d ' ' -f 2)" != "$STUDIO_UV_VERSION" ]; then
  ln -sfn ../toolchains/uv/uv .runtime/bin/uv
fi
if [ "$STUDIO_PYTHON_ONLY" = 0 ]; then
  install_archive node "$STUDIO_NODE_VERSION" "$STUDIO_NODE_URL" 256 "$STUDIO_NODE_SHA256"
  install_archive pnpm "$STUDIO_PNPM_VERSION" "$STUDIO_PNPM_URL" 512 "$STUDIO_PNPM_SHA512"
  install_archive java "$STUDIO_JAVA_VERSION" "$STUDIO_JAVA_URL" 256 "$STUDIO_JAVA_SHA256"
  install_archive maven "$STUDIO_MAVEN_VERSION" "$STUDIO_MAVEN_URL" 512 "$STUDIO_MAVEN_SHA512"
  . ./scripts/runtime-env.sh
fi
.runtime/bin/uv python install --no-bin "$STUDIO_PYTHON_VERSION"
.runtime/bin/uv venv .venv --allow-existing --relocatable --managed-python --python "$STUDIO_PYTHON_VERSION"
.runtime/bin/uv sync --locked --python "$STUDIO_PYTHON_VERSION"
PYTHONPATH="$PROJECT_ROOT/src:$PROJECT_ROOT/vendor" .venv/bin/python -c 'from voice_cloner.cli import _ensure_local_environment; _ensure_local_environment()'
.venv/bin/python scripts/repair-runtime-locations.py
if [ "$STUDIO_PYTHON_ONLY" = 0 ]; then
  CI=true .runtime/toolchains/node/bin/node .runtime/toolchains/pnpm/bin/pnpm.cjs --dir frontend install --frozen-lockfile
  .runtime/toolchains/node/bin/node .runtime/toolchains/pnpm/bin/pnpm.cjs --dir frontend build
  ./scripts/server.sh build
fi
printf 'Готово. Всё установлено внутри проекта.\n'
if [ "$STUDIO_PYTHON_ONLY" = 0 ]; then printf 'Запуск: ./scripts/studio.sh\n'; else printf 'Проверка: ./voice doctor\n'; fi
