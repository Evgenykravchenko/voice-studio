#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"
. ./scripts/runtime-env.sh
case "${1:-}" in
  --dev) STUDIO_DEV=1; shift ;;
  '') STUDIO_DEV=0 ;;
  *) echo 'Использование: ./scripts/studio.sh [--dev]' >&2; exit 2 ;;
esac
if [ ! -x .venv/bin/python ] || ! .venv/bin/python scripts/check-runtime-location.py || [ ! -f frontend/dist/client/index.html ] || [ ! -f server/target/voice-studio-server-0.1.1.jar ]; then
  ./scripts/bootstrap.sh
  . ./scripts/runtime-env.sh
fi
if .venv/bin/python scripts/check-studio.py --port 4173 --root "$PROJECT_ROOT"; then
  echo 'Voice Studio уже запущена: http://127.0.0.1:4173'; exit 0
else
  STUDIO_PORT_STATUS=$?
  if [ "$STUDIO_PORT_STATUS" = 2 ]; then echo 'Порт4173 занят другим сервером. Освободите его перед запуском студии.' >&2; exit 1; fi
fi
if [ "$STUDIO_DEV" = 0 ]; then
  echo 'Voice Studio: http://127.0.0.1:4173 (остановить: Ctrl+C)'
  exec ./scripts/server.sh --studio
fi
STUDIO_NODE="$PROJECT_ROOT/.runtime/toolchains/node/bin/node"
if [ ! -x "$STUDIO_NODE" ]; then STUDIO_NODE=$(command -v node || true); fi
if [ ! -x "$STUDIO_NODE" ]; then echo 'Не найдена Node.js. Выполните ./scripts/bootstrap.sh.' >&2; exit 1; fi
if [ ! -f frontend/node_modules/vite/bin/vite.js ]; then echo 'Не установлены библиотеки интерфейса. Выполните ./scripts/bootstrap.sh.' >&2; exit 1; fi
mkdir -p .runtime/logs
STUDIO_SERVER_PID=
STUDIO_FRONTEND_PID=
cleanup() {
  trap - EXIT INT TERM
  [ -z "$STUDIO_FRONTEND_PID" ] || kill "$STUDIO_FRONTEND_PID" 2>/dev/null || true
  [ -z "$STUDIO_SERVER_PID" ] || kill "$STUDIO_SERVER_PID" 2>/dev/null || true
  [ -z "$STUDIO_FRONTEND_PID" ] || wait "$STUDIO_FRONTEND_PID" 2>/dev/null || true
  [ -z "$STUDIO_SERVER_PID" ] || wait "$STUDIO_SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if ! .venv/bin/python scripts/check-studio.py --port 7080 --root "$PROJECT_ROOT"; then
  ./scripts/server.sh >> .runtime/logs/java-server.log 2>&1 &
  STUDIO_SERVER_PID=$!
  STUDIO_READY=0
  for STUDIO_ATTEMPT in $(seq 1 120); do
    if .venv/bin/python scripts/check-studio.py --port 7080 --root "$PROJECT_ROOT"; then STUDIO_READY=1; break; fi
    kill -0 "$STUDIO_SERVER_PID" 2>/dev/null || break
    sleep .25
  done
  [ "$STUDIO_READY" = 1 ] || { echo 'API не запустился. Проверьте .runtime/logs/java-server.log.' >&2; exit 1; }
fi
cd frontend
"$STUDIO_NODE" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 4173 --strictPort "$@" &
STUDIO_FRONTEND_PID=$!
echo 'Voice Studio (разработка): http://127.0.0.1:4173'
wait "$STUDIO_FRONTEND_PID"
