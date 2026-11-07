#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$PROJECT_ROOT/scripts/runtime-env.sh"
if [ ! -x "$PROJECT_ROOT/.runtime/toolchains/node/bin/node" ] || [ ! -f "$PROJECT_ROOT/.runtime/toolchains/pnpm/bin/pnpm.mjs" ]; then
  echo 'Не найдены локальные Node.js и pnpm. Выполните ./scripts/bootstrap.sh.' >&2; exit 1
fi
# pnpm's ESM entry point reuses this interpreter for nested installs. The CJS
# compatibility shim instead looks for a separate pnpm command on PATH.
exec "$PROJECT_ROOT/.runtime/toolchains/node/bin/node" "$PROJECT_ROOT/.runtime/toolchains/pnpm/bin/pnpm.mjs" "$@"
