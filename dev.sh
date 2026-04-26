#!/usr/bin/env bash
# One entry point for common project commands. From the repo root:
#   chmod +x dev.sh   # once, if your filesystem allows execute bits
#   ./dev.sh help
#   bash dev.sh help  # works everywhere (e.g. some network volumes block +x)
#   ./dev.sh test
#   ./dev.sh test tests/test_admin_api.py -q
#   ./dev.sh test -- -k admin -x
#   CONFIG=my.yaml ./dev.sh dry-run
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VENV_PY="$ROOT/.venv/bin/python"
VENV_PIP="$ROOT/.venv/bin/pip"
VENV_PYTEST="$ROOT/.venv/bin/pytest"

if [[ -x "$VENV_PY" ]]; then
  PY="$VENV_PY"
  PIP=("$VENV_PIP")
  PYTEST=("$VENV_PYTEST")
else
  PY="${PYTHON:-python3}"
  PIP=("$PY" -m pip)
  PYTEST=("$PY" -m pytest)
fi

CONFIG="${CONFIG:-config.yaml}"
NPM_DIR="$ROOT/admin-ui"

usage() {
  cat <<'EOF'
dev.sh — Twitter bot project runner

Commands:
  help              Show this message
  setup             Create .venv (if missing) and pip install -r requirements.txt
  test [pytest…]    Run pytest (removes stale .coverage first); extra args go to pytest
  bootstrap         bot.py bootstrap --config CONFIG
  start             bot.py start --config CONFIG
  dry-run           bot.py dry-run --config CONFIG
  stop              bot.py stop --config CONFIG
  resume            bot.py resume --config CONFIG
  status            bot.py status --config CONFIG
  admin             run_admin.py (ADMIN_BIND / ADMIN_PORT / ADMIN_TOKEN from env)
  admin-build       npm ci + npm run build in admin-ui/
  admin-dev         npm install + npm run dev in admin-ui/ (proxies to API)

Environment:
  CONFIG            Config path for bot.py commands (default: config.yaml)
  PYTHON            Python to use when .venv is missing (default: python3)

Examples:
  ./dev.sh test
  ./dev.sh test -- -k admin -x
  CONFIG=config.yaml ./dev.sh dry-run
EOF
}

npm_admin() {
  (cd "$NPM_DIR" && "$@")
}

case "${1:-help}" in
  help|-h|--help)
    usage
    ;;
  setup|install)
    if [[ ! -x "$VENV_PY" ]]; then
      "$PY" -m venv "$ROOT/.venv"
    fi
    "${PIP[@]}" install -r "$ROOT/requirements.txt"
    ;;
  test|tests)
    shift
    rm -f "$ROOT/.coverage"
    exec "${PYTEST[@]}" "$@"
    ;;
  bootstrap)
    exec "$PY" "$ROOT/bot.py" bootstrap --config "$CONFIG"
    ;;
  start)
    exec "$PY" "$ROOT/bot.py" start --config "$CONFIG"
    ;;
  dry-run|dryrun)
    exec "$PY" "$ROOT/bot.py" dry-run --config "$CONFIG"
    ;;
  stop)
    exec "$PY" "$ROOT/bot.py" stop --config "$CONFIG"
    ;;
  resume)
    exec "$PY" "$ROOT/bot.py" resume --config "$CONFIG"
    ;;
  status)
    exec "$PY" "$ROOT/bot.py" status --config "$CONFIG"
    ;;
  admin)
    exec "$PY" "$ROOT/run_admin.py"
    ;;
  admin-build)
    npm_admin npm ci
    npm_admin npm run build
    ;;
  admin-dev)
    npm_admin npm install
    npm_admin npm run dev
    ;;
  *)
    echo "Unknown command: ${1:-}" >&2
    echo >&2
    usage >&2
    exit 1
    ;;
esac
