#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"
. ./scripts/runtime-env.sh
if [ -z "${VOICE_JAVA_HOME:-}" ]; then
  if [ -x "$PROJECT_ROOT/.runtime/toolchains/java/Contents/Home/bin/java" ]; then
    VOICE_JAVA_HOME="$PROJECT_ROOT/.runtime/toolchains/java/Contents/Home"
  else
    VOICE_JAVA_HOME=$(/usr/libexec/java_home -v 21 -a arm64 2>/dev/null || true)
  fi
fi
if [ ! -x "$VOICE_JAVA_HOME/bin/java" ]; then echo 'Не найдена Java21. Выполните ./scripts/bootstrap.sh.' >&2; exit 1; fi
export JAVA_HOME="$VOICE_JAVA_HOME"
export PATH="$JAVA_HOME/bin:$PATH"
case "${1:-}" in
  build|test)
    STUDIO_MAVEN="$PROJECT_ROOT/.runtime/toolchains/maven/bin/mvn"
    [ -x "$STUDIO_MAVEN" ] || STUDIO_MAVEN="$PROJECT_ROOT/.runtime/maven/bin/mvn"
    [ -x "$STUDIO_MAVEN" ] || { echo 'Не найден локальный Maven. Выполните ./scripts/bootstrap.sh.' >&2; exit 1; }
    STUDIO_GOAL=test
    if [ "$1" = build ]; then
      STUDIO_GOAL=package
      for STUDIO_PORT in 4173 7080; do
        if [ -x .venv/bin/python ] && .venv/bin/python scripts/check-studio.py --port "$STUDIO_PORT" --root "$PROJECT_ROOT"; then
          echo 'Студия этого проекта запущена. Остановите её перед сборкой сервера, чтобы не перезаписывать работающий JAR.' >&2; exit 1
        fi
      done
    fi
    exec "$STUDIO_MAVEN" -B -q -Dmaven.repo.local="$PROJECT_ROOT/.runtime/cache/maven" -f server/pom.xml "$STUDIO_GOAL"
    ;;
  --studio) STUDIO_PORT=4173 ;;
  '') STUDIO_PORT=7080 ;;
  *) echo 'Использование: ./scripts/server.sh [build|test|--studio]' >&2; exit 2 ;;
esac
if [ ! -f server/target/voice-studio-server-0.1.1.jar ]; then echo 'Сервер не собран. Выполните ./scripts/bootstrap.sh.' >&2; exit 1; fi
exec "$JAVA_HOME/bin/java" -Xms64m -Xmx384m -Dvoice.project="$PROJECT_ROOT" -Dserver.port="$STUDIO_PORT" -jar server/target/voice-studio-server-0.1.1.jar
