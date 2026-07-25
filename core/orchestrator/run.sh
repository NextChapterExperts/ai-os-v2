#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"
export AIOS_BRAIN_SEED="${AIOS_BRAIN_SEED:-$ROOT/customers/nextchapter/knowledge/seed/brain.json}"
export AIOS_MEMORY_DB="${AIOS_MEMORY_DB:-/opt/ai-os/memory/memory.db}"
export LITELLM_URL="${LITELLM_URL:-http://127.0.0.1:4000}"
# Projekt-Slug haengt vom Cursor-Workspace-Root ab (core/capture/cursor-job.mjs);
# seit die Workspace-Root Projekte/ ist, heisst er "home-peter-Projekte" statt
# des alten "...-1100-AI-OS-V2"-Scopes (siehe memory_store.py).
export AIOS_MEMORY_PROJECT="${AIOS_MEMORY_PROJECT:-home-peter-Projekte}"
if [[ -f "$ROOT/.env" ]]; then set -a; source "$ROOT/.env"; set +a; fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
exec python -m uvicorn core.orchestrator.server:app --host 0.0.0.0 --port "${ORCHESTRATOR_PORT:-8091}"
