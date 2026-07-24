#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PYTHONPATH="$ROOT"
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
exec python -m uvicorn core.mcp_gateway.server:app --host 0.0.0.0 --port "${MCP_GATEWAY_PORT:-8097}"
