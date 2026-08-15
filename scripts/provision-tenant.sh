#!/usr/bin/env bash
# ==============================================================================
# scripts/provision-tenant.sh — Mandanten-Initialisierung für AI-OS v2 Appliance
#
# Verwendung:
#   ./scripts/provision-tenant.sh <tenant_id> "<Company Name>" ["<Branche>"]
# ==============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ $# -lt 2 ]]; then
  echo "Verwendung: $0 <tenant_id> \"<Company Name>\" [\"<Branche>\"]"
  echo "Beispiel:   $0 kanzlei_schmidt \"Rechtsanwälte Schmidt & Partner\" \"Rechtsberatung\""
  exit 1
fi

TENANT_ID="$1"
COMPANY_NAME="$2"
INDUSTRY="${3:-Allgemeine Unternehmensberatung & Dienstleistungen}"

export PYTHONPATH="$ROOT"
source "$ROOT/.venv/bin/activate"

python3 - <<EOF
from core.orchestrator.tenant_provisioning import provision_tenant

res = provision_tenant(
    tenant_id="${TENANT_ID}",
    company_name="${COMPANY_NAME}",
    industry="${INDUSTRY}",
)
print(f"✅ Mandant '{res['tenant_id']}' erfolgreich provisioniert!")
print(f"📁 Pfad: {res['tenant_dir']}")
print(f"🧠 Company Brain: {res['knowledge_dir']}/00-company-profile.yaml")
EOF
