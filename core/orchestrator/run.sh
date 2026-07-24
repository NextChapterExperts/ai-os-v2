#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"
export AIOS_BRAIN_SEED="${AIOS_BRAIN_SEED:-$ROOT/customers/nextchapter/knowledge/seed/brain.json}"
export AIOS_MEMORY_DB="${AIOS_MEMORY_DB:-/opt/ai-os/memory/memory.db}"
export AIOS_MEMORY_PROJECT="${AIOS_MEMORY_PROJECT:-home-peter-Projekte-1100-AI-OS-V2}"
if [[ -f "$ROOT/.env" ]]; then set -a; source "$ROOT/.env"; set +a; fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
exec python -m uvicorn core.orchestrator.server:app --host 0.0.0.0 --port "${ORCHESTRATOR_PORT:-8091}"
