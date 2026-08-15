#!/usr/bin/env bash
# ==============================================================================
# scripts/export-core-appliance.sh
# Exportiert die reine AI-OS v2 Core Plattform Appliance in ein autarkes
# Distributions-Projekt (1110-AI-OS-Core-Platform) ohne R&D-Artefakte.
# ==============================================================================
set -euo pipefail

SRC_DIR="/home/peter/Projekte/1100-AI-OS-V2"
TARGET_DIR="/home/peter/Projekte/1110-AI-OS-Core-Platform"

echo "🚀 Starte Export der Core Plattform Appliance..."
echo "📂 Quelle: ${SRC_DIR}"
echo "🎯 Ziel:   ${TARGET_DIR}"

# 1. Zielverzeichnis vorbereiten
mkdir -p "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}/core/orchestrator"
mkdir -p "${TARGET_DIR}/core/memory"
mkdir -p "${TARGET_DIR}/core/memory_gateway"
mkdir -p "${TARGET_DIR}/core/workflow_engine"
mkdir -p "${TARGET_DIR}/core/file_ingest_watcher"
mkdir -p "${TARGET_DIR}/core/ingest_agent"
mkdir -p "${TARGET_DIR}/core/console-web"
mkdir -p "${TARGET_DIR}/sdk"
mkdir -p "${TARGET_DIR}/config"
mkdir -p "${TARGET_DIR}/deploy"
mkdir -p "${TARGET_DIR}/tests"
mkdir -p "${TARGET_DIR}/docs"
mkdir -p "${TARGET_DIR}/scripts"

# 2. Core Plattform Backend-Module kopieren
echo "📦 Kopiere alle Core Plattform Backend-Module..."
rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/orchestrator/" "${TARGET_DIR}/core/orchestrator/"

rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/memory/" "${TARGET_DIR}/core/memory/"

rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/memory_gateway/" "${TARGET_DIR}/core/memory_gateway/"

rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/workflow_engine/" "${TARGET_DIR}/core/workflow_engine/"

rsync -av --exclude '__pycache__' --exclude '*.pyc' --exclude '.venv' \
  "${SRC_DIR}/core/file_ingest_watcher/" "${TARGET_DIR}/core/file_ingest_watcher/"

rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/ingest_agent/" "${TARGET_DIR}/core/ingest_agent/"

# 3. Agent SDK & Schemas kopieren
echo "🧩 Kopiere Agent SDK & Developer Kit..."
rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/sdk/" "${TARGET_DIR}/sdk/"

# 4. Plattform-Konfigurationen kopieren
echo "⚙️ Kopiere Plattform-Konfigurationen & SQL-Schemata..."
rsync -av --exclude '__pycache__' \
  "${SRC_DIR}/config/" "${TARGET_DIR}/config/"

# 5. Deployment-Setups kopieren
echo "🐳 Kopiere Deployment-Setups & Docker Stacks..."
rsync -av "${SRC_DIR}/deploy/" "${TARGET_DIR}/deploy/"

# 6. Reines Web Frontend kopieren
echo "🌐 Kopiere Core Web Konsole (Next.js)..."
rsync -av --exclude 'node_modules' --exclude '.next' --exclude '.git' \
  "${SRC_DIR}/core/console-web/" "${TARGET_DIR}/core/console-web/"

# 7. Plattform-Testsuite kopieren
echo "🧪 Kopiere Plattform-Testsuite..."
rsync -av --exclude '__pycache__' --exclude '.pytest_cache' \
  "${SRC_DIR}/tests/" "${TARGET_DIR}/tests/"

# 8. Konfigurations- & Root-Dateien kopieren
if [ -f "${SRC_DIR}/core/orchestrator/requirements.txt" ]; then
  cp -f "${SRC_DIR}/core/orchestrator/requirements.txt" "${TARGET_DIR}/requirements.txt"
fi
if [ -f "${SRC_DIR}/.env.example" ]; then
  cp -f "${SRC_DIR}/.env.example" "${TARGET_DIR}/"
fi
if [ -f "${SRC_DIR}/.gitignore" ]; then
  cp -f "${SRC_DIR}/.gitignore" "${TARGET_DIR}/"
fi

# 9. Vollständige CLI & Speichermanagement-Skripte kopieren
echo "🛠️ Kopiere alle Speichermanagement-, Ingest-, Test- & Plattform-Skripte..."
SCRIPTS_TO_EXPORT=(
  "run-all-tests.sh"
  "run-l1-curator.py"
  "run-l2-curator.py"
  "run-l3-curator.py"
  "rebuild-fts.py"
  "backfill-letta-from-sqlite.py"
  "provision-tenant.sh"
  "search_company_brain.py"
  "manage_memory.py"
  "ingest_documents.py"
  "manage_company_profile.py"
  "run-memory-testcases.py"
  "generate-memory-testcases.py"
  "run-compute-mode-testcases.py"
)

for s in "${SCRIPTS_TO_EXPORT[@]}"; do
  if [ -f "${SRC_DIR}/scripts/${s}" ]; then
    cp -f "${SRC_DIR}/scripts/${s}" "${TARGET_DIR}/scripts/"
  fi
done
chmod +x "${TARGET_DIR}"/scripts/*

# 6. Vollständige Original-Plattform-Dokumentation kopieren
echo "📚 Kopiere alle vollständigen Original-Dokumente aus docs/..."

DOC_FILES=(
  "00-VISION.md"
  "01-ARCHITEKTUR.md"
  "02-AGENT-SDK.md"
  "03-DATENPRODUKTE.md"
  "04-DEPLOYMENT.md"
  "05-CONSOLE-IA.md"
  "06-PRODUKT-DEPLOYMENT.md"
  "07-LOKALES-MODELL-TESTPROTOKOLL.md"
  "08-MARKTVERGLEICH.md"
  "09-COMPANY-BRAIN.md"
  "10-MEMORY-EINFACH.md"
  "11-PLATFORM-VM.md"
  "12-LEITPRINZIPIEN.md"
  "13-IST-STAND.md"
  "14-KONTEXT.md"
  "15-FILE-INGESTION.md"
  "16-VM-PACKAGING.md"
  "22-RELEASE-TAGS.md"
  "23-DOCKER-MCP-SANDBOX-INTEGRATION.md"
  "25-COMPANY-BRAIN-MEMORY-MAPPING.md"
  "26-ARTEN-VON-RAG.md"
  "27-ROLLEN-UND-RECHTE-KONZEPT.md"
  "28-PLATFORM-VS-CUSTOM-AGENTS-MODELL.md"
  "29-STAGING-UND-VM-RELEASE-WORKFLOW.md"
  "30-CORE-PLATFORM-EXTRACTION-UND-DOCKER-CONTAINER.md"
  "31-CORE-PLATFORM-DISTRIBUTION-REPO.md"
  "32-PLATFORM-AUDITLOG-UND-DISTRIBUTION-GIT.md"
  "company_brain_paper_DE.pdf"
)

for doc in "${DOC_FILES[@]}"; do
  if [ -f "${SRC_DIR}/docs/${doc}" ]; then
    cp -f "${SRC_DIR}/docs/${doc}" "${TARGET_DIR}/docs/"
  fi
done

if [ -d "${SRC_DIR}/docs/adr" ]; then
  rsync -av "${SRC_DIR}/docs/adr/" "${TARGET_DIR}/docs/adr/"
fi

# Zusätzliches Handbuch für CLI Tools
cat << "EOF" > "${TARGET_DIR}/docs/00-CLI-UND-ADMIN-HANDBUCH.md"
# 00 — CLI- & Administrations-Handbuch

Die Plattform verfügt über dedizierte Skripte im Verzeichnis \`scripts/\`:

### 1. Wissenssuche im Terminal (\`scripts/search_company_brain.py\`)
\`\`\`bash
python3 scripts/search_company_brain.py "Welche Zahlungsfristen gelten für Großkunden?" --tenant default
\`\`\`

### 2. Memory- & Speicherverwaltung (\`scripts/manage_memory.py\`)
\`\`\`bash
python3 scripts/manage_memory.py --status
\`\`\`

### 3. Dokumenten- & PDF-Ingestion (\`scripts/ingest_documents.py\`)
\`\`\`bash
# Einzelne Datei ingestieren
python3 scripts/ingest_documents.py /pfad/zum/vertrag.pdf --tenant default

# Ganzen Ordner batch-ingestieren
python3 scripts/ingest_documents.py /pfad/zu/dokumenten/ --tenant default
\`\`\`

### 4. Firmenprofil per CLI (\`scripts/manage_company_profile.py\`)
\`\`\`bash
# Profil anzeigen
python3 scripts/manage_company_profile.py --tenant default

# Profil aktualisieren
python3 scripts/manage_company_profile.py --update-from neues_profil.yaml --tenant default
\`\`\`
EOF

# 7. Readme für das Distributions-Repo
cat << "EOF" > "${TARGET_DIR}/README.md"
# AI-OS Core Platform Appliance (v1.0.0)

> **Sovereign Enterprise Memory & Knowledge Platform**  
> Offizielles Distributions-Repository der reinen AI-OS Core Appliance.

## 🚀 Schnellstart

\`\`\`bash
# Docker Stack starten
cd deploy/docker
docker compose up -d
\`\`\`

- **Web-Konsole:** [http://localhost:8090](http://localhost:8090)
- **Orchestrator API:** [http://localhost:8091/docs](http://localhost:8091/docs)

## 🛠️ CLI & Management Werkzeuge

- **Suche im Unternehmenswissen:** `python3 scripts/search_company_brain.py "<Query>"`
- **Speicherstatus & Memory Stacks:** `python3 scripts/manage_memory.py --status`
- **Dokumenten-Ingestion:** `python3 scripts/ingest_documents.py <Pfad>`
- **Unternehmensprofil:** `python3 scripts/manage_company_profile.py`

## 📚 Dokumentation
Die vollständige Architektur-Dokumentation befindet sich im Verzeichnis [`docs/`](docs/).
EOF

# 8. Git Sync & GitHub Distribution Push
cd "${TARGET_DIR}"
git branch -M main || true
TOKEN=$(git -C "${SRC_DIR}" config --get remote.origin.url | sed -n 's/.*x-access-token:\([^@]*\)@.*/\1/p' || true)
if [ -n "${TOKEN}" ]; then
  AUTH_REMOTE="https://x-access-token:${TOKEN}@github.com/NextChapterExperts/virgi-platform-dist.git"
else
  AUTH_REMOTE="https://github.com/NextChapterExperts/virgi-platform-dist.git"
fi

if ! git remote | grep -q "origin"; then
  git remote add origin "${AUTH_REMOTE}"
else
  git remote set-url origin "${AUTH_REMOTE}"
fi

git add .
git commit -m "feat(release): AI-OS Core Platform Appliance v1.0.0

- Revisionssicherer Release-Changelog & Auditlog
- 5-Schichten-Memory-Modell & Hybrid Graph-RAG
- Unternehmens-Identität & Dynamische Profilverwaltung (/company)
- Multi-Stage Dockerfile & Docker Compose Setup
- CLI Management Toolbox (search, memory, ingest, company profile)
- Vollständige Architektur- & Kunden-Dokumentation (docs/01-06)" || true

git tag -f v1.0.0-core-appliance -m "AI-OS Core Platform Appliance v1.0.0"

echo "📡 Pushe Release nach GitHub (virgi-platform-dist)..."
git push -u origin main --tags --force

echo "✅ Core Plattform Appliance & CLI-Skripte erfolgreich nach ${TARGET_DIR} exportiert und gepusht!"
