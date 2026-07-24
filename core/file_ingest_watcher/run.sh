#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/.venv/bin/activate"
exec python "$ROOT/watcher.py" "$@"
