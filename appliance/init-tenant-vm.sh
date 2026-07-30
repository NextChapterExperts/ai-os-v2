#!/usr/bin/env bash
# AI-OS v2 — Customer Onboarding & Tenant VM Initialization Script
# Richtet eine neue Platform-VM für einen Mandanten ein.
# Usage: ./appliance/init-tenant-vm.sh --tenant <tenant_id> --domain <domain> [--openrouter-key <key>]

set -euo pipefail

TENANT_ID=""
DOMAIN="localhost"
OPENROUTER_KEY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tenant)
      TENANT_ID="$2"
      shift 2
      ;;
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    --openrouter-key)
      OPENROUTER_KEY="$2"
      shift 2
      ;;
    *)
      echo "Unbekannter Parameter: $1"
      exit 1
      ;;
  esac
done

if [ -z "$TENANT_ID" ]; then
  echo "Fehler: Parameter --tenant <tenant_id> ist erforderlich."
  echo "Beispiel: ./appliance/init-tenant-vm.sh --tenant malerbetrieb-schulze --domain schulze.ai-os.local"
  exit 1
fi

echo "======================================================================"
echo "          AI-OS v2 — Mandanten-VM Initialisierung"
echo "======================================================================"
echo "Mandant ID:  ${TENANT_ID}"
echo "Domain:      ${DOMAIN}"
echo "----------------------------------------------------------------------"

AIOS_DIR="/opt/ai-os"
mkdir -p "${AIOS_DIR}/config" "${AIOS_DIR}/memory/state" "${AIOS_DIR}/ingest/inbox"

# 1. Schreib Mandanten-Konfiguration
ENV_FILE="${AIOS_DIR}/.env"
cat <<EOF > "$ENV_FILE"
# AI-OS Mandanten-Konfiguration (${TENANT_ID})
TENANT_ID=${TENANT_ID}
DOMAIN=${DOMAIN}
AIOS_MEMORY_DB=${AIOS_DIR}/memory/memory.db
AIOS_INGEST_INBOX=${AIOS_DIR}/ingest/inbox
DEFAULT_COMPUTE_MODE=sovereign
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434
OPENROUTER_API_KEY=${OPENROUTER_KEY}
EOF

chmod 600 "$ENV_FILE"
echo "✓ Mandanten-Konfiguration geschrieben: ${ENV_FILE}"

# 2. Erstelle Tenant State File
STATE_FILE="${AIOS_DIR}/memory/state/tenant-info.json"
cat <<EOF > "$STATE_FILE"
{
  "tenant_id": "${TENANT_ID}",
  "domain": "${DOMAIN}",
  "initialized_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "status": "active"
}
EOF

echo "✓ Tenant-Status initialisiert: ${STATE_FILE}"

# 3. Datenbank-Schema sicherstellen & Seed
echo "✓ Bereite Memory DB & Ingestion vor..."
python3 -c "
import os, sqlite3
from pathlib import Path
db_path = Path('${AIOS_DIR}/memory/memory.db')
db_path.parent.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(db_path)
con.execute('CREATE TABLE IF NOT EXISTS tenant_meta (key TEXT PRIMARY KEY, value TEXT)')
con.execute('INSERT OR REPLACE INTO tenant_meta VALUES (?, ?)', ('tenant_id', '${TENANT_ID}'))
con.commit()
con.close()
print('✓ Memory DB für Mandant', '${TENANT_ID}', 'geseedet.')
"

echo "======================================================================"
echo "✓ Mandanten-VM '${TENANT_ID}' erfolgreich initialisiert!"
echo "Console URL: http://${DOMAIN}:8092"
echo "API URL:     http://${DOMAIN}:8091"
echo "======================================================================"
