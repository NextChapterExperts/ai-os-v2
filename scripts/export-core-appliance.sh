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
mkdir -p "${TARGET_DIR}/core/console-web"
mkdir -p "${TARGET_DIR}/deploy/docker"
mkdir -p "${TARGET_DIR}/docs"
mkdir -p "${TARGET_DIR}/scripts"

# 2. Reines Orchestrator Backend kopieren
echo "📦 Kopiere Core Orchestrator Module..."
rsync -av --exclude '__pycache__' --exclude '*.pyc' \
  "${SRC_DIR}/core/orchestrator/" "${TARGET_DIR}/core/orchestrator/"

# 3. Reines Web Frontend kopieren
echo "🌐 Kopiere Core Web Konsole (Next.js)..."
rsync -av --exclude 'node_modules' --exclude '.next' --exclude '.git' \
  "${SRC_DIR}/core/console-web/" "${TARGET_DIR}/core/console-web/"

# 4. Docker Deployment Stack kopieren
echo "🐳 Kopiere Docker Appliance Stack..."
rsync -av "${SRC_DIR}/deploy/docker/" "${TARGET_DIR}/deploy/docker/"

# 5. CLI & Administrations-Skripte kopieren
echo "🛠️ Kopiere CLI- & Management-Skripte..."
cp -f "${SRC_DIR}/scripts/search_company_brain.py" "${TARGET_DIR}/scripts/"
cp -f "${SRC_DIR}/scripts/manage_memory.py" "${TARGET_DIR}/scripts/"
cp -f "${SRC_DIR}/scripts/ingest_documents.py" "${TARGET_DIR}/scripts/"
cp -f "${SRC_DIR}/scripts/manage_company_profile.py" "${TARGET_DIR}/scripts/"
chmod +x "${TARGET_DIR}"/scripts/*.py

# 6. Top-Tier Plattform-Dokumentation erstellen & kopieren
echo "📚 Erstelle umfassende Plattform-Dokumentation..."

cat << "EOF" > "${TARGET_DIR}/docs/01-ARCHITEKTUR-UEBERSICHT.md"
# 01 — AI-OS Core Platform Architektur-Übersicht

AI-OS Core ist eine hochperformante, DSGVO-konforme Enterprise-Appliance für das Wissens- und Memory-Management von Unternehmen.

## Kernkomponenten:
1. **5-Layer Memory Model:** Deterministisches Gedächtnis von Live-Arbeitskontext bis zur Unternehmens-DNA.
2. **Hybrid Graph-RAG:** Multi-Hop Wissensgraph kombiniert mit dichter Vektorsuche für halluzinationsfreie Antworten.
3. **Enterprise Identity Root:** Zentrales, kanonisches Unternehmensprofil als Fundament für alle Workflows.
4. **Sovereign Multi-Tenant Isolation:** Vollständige Trennung von Mandantendaten auf Dateisystem- und Datenbankebene.
EOF

cat << "EOF" > "${TARGET_DIR}/docs/02-5-SCHICHTEN-MEMORY-MODELL.md"
# 02 — Das 5-Schichten-Memory-Modell

Die Plattform implementiert ein hierarchisches, kognitives Speichermodell:

| Schicht | Name | Funktion | Technologie |
|---|---|---|---|
| **L1** | Working Memory | Aktuelle Interaktion / Chat-Session | RAM / Redis / FastCache |
| **L2** | Episodic Memory | Ereignisse, Meetings, Protokolle | SQLite / JSONL |
| **L3** | Semantic Chunks | Dokumente, PDFs, Rechnungen, Verträge | Dense Vector Embeddings |
| **L4** | Knowledge Graph | Beziehungen, Entitäten, Multi-Hop | Property Graph |
| **L5** | Enterprise Core | Statuten, Richtlinien, Organigramm | Kanonisches YAML / Graph Root |
EOF

cat << "EOF" > "${TARGET_DIR}/docs/03-HYBRID-GRAPH-RAG-SUCHE.md"
# 03 — Hybrid Graph-RAG Sucharchitektur

Die Suche verbindet zwei komplementäre Retrieval-Verfahren:
- **Dichte Vektorsuche:** Findet semantisch ähnliche Textabschnitte auch bei ungenauen Suchbegriffen.
- **Wissensgraph-Traversal:** Folgt expliziten Relationen (z.B. Person -> Projekt -> Vertrag) mit 100% Faktentreue.
- **Fusion:** Ein Reciprocal Rank Fusion (RRF) Algorithmus vereint beide Ergebnisse zu einer optimalen Rangfolge.
EOF

cat << "EOF" > "${TARGET_DIR}/docs/04-UNTERNEHMENS-IDENTITAET.md"
# 04 — Unternehmens-Identität (Company Brain Root)

Jeder Mandant besitzt ein kanonisches Profil (`00-company-profile.yaml`):
- Offizieller Firmenname, Marke, Rechtsform, USt-ID
- Stundensätze und Standard-Zahlungsbedingungen
- Mitarbeiter, Rollen und Fähigkeiten
- Kern-Dienstleistungen und Tätigkeitsfelder

Dieses Profil wird automatisch in jeden Abfragekontext (`ContextBundle.enterprise`) injiziert.
EOF

cat << "EOF" > "${TARGET_DIR}/docs/05-DOCKER-UND-PROVISIONIERUNG.md"
# 05 — Docker & Cloud Provisionierung

## 1. Lokaler Start via Docker Compose:
\`\`\`bash
cd deploy/docker
docker compose up -d
\`\`\`
Die Konsole ist sofort erreichbar unter: `http://localhost:8090`

## 2. Google Cloud Run Deployment:
\`\`\`bash
gcloud run deploy aios-core-appliance \
  --image=gcr.io/PROJECT_ID/aios-core-appliance:latest \
  --region=europe-west3 \
  --allow-unauthenticated
\`\`\`
EOF

cat << "EOF" > "${TARGET_DIR}/docs/06-CLI-UND-ADMIN-TOOLS.md"
# 06 — CLI- & Administrations-Werkzeuge

Die Plattform verfügt über dedizierte Skripte im Verzeichnis `scripts/`:

### 1. Wissenssuche im Terminal (`scripts/search_company_brain.py`)
\`\`\`bash
python3 scripts/search_company_brain.py "Welche Zahlungsfristen gelten für Großkunden?" --tenant default
\`\`\`

### 2. Memory- & Speicherverwaltung (`scripts/manage_memory.py`)
\`\`\`bash
python3 scripts/manage_memory.py --status
\`\`\`

### 3. Dokumenten- & PDF-Ingestion (`scripts/ingest_documents.py`)
\`\`\`bash
# Einzelne Datei ingestieren
python3 scripts/ingest_documents.py /pfad/zum/vertrag.pdf --tenant default

# Ganzen Ordner batch-ingestieren
python3 scripts/ingest_documents.py /pfad/zu/dokumenten/ --tenant default
\`\`\`

### 4. Firmenprofil per CLI (`scripts/manage_company_profile.py`)
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
