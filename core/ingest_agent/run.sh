#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
if [[ -f "$ROOT/.env" ]]; then set -a; source "$ROOT/.env"; set +a; fi
source "$ROOT/.venv/bin/activate"
exec python core/ingest_agent/ingest.py "$@"
