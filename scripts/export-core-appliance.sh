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

# 5. Top-Tier Plattform-Dokumentation erstellen & kopieren
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

# 6. Readme für das Distributions-Repo
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

## 📚 Dokumentation
Die vollständige Architektur-Dokumentation befindet sich im Verzeichnis [`docs/`](docs/).
EOF

# 7. Git Initialisierung im Ziel-Repo (falls noch nicht geschehen)
cd "${TARGET_DIR}"
if [ ! -d ".git" ]; then
  git init
  git config user.name "Peter Alexander"
  git config user.email "peter.alexander@nextchapterexperts.de"
fi

git add .
git commit -m "feat(release): initialize AI-OS Core Platform Distribution v1.0.0

- Extracted clean platform sources from 1100-AI-OS-V2
- 5-layer cognitive memory architecture & hybrid Graph-RAG
- Dynamic enterprise profile management (/company)
- Unified multi-stage production Dockerfile & compose stack
- Comprehensive customer and admin documentation" || true

git tag -f v1.0.0-core-appliance -m "AI-OS Core Platform Appliance v1.0.0"

echo "✅ Core Plattform Appliance erfolgreich nach ${TARGET_DIR} exportiert!"
