# AI-OS v2 — Deployment: 3 Modi

**Stand:** Juli 2026 (Platform-VM 2026-07-24) · **Verwandt:** [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) · [11-PLATFORM-VM.md](11-PLATFORM-VM.md) · [ROADMAP.md](../ROADMAP.md)

---

## Platform-VM zuerst (P19)

Auslieferung und Betrieb laufen **in einer Linux-VM** (KVM/qcow2 bzw. Hetzner-VM):

| Profil | Inhalt |
|--------|--------|
| **DEV-VM** | Ubuntu Desktop · Cursor · Antigravity · Docker Compose (Infra→Core→…) |
| **PROD-VM** | Ubuntu Server · nur Compose + Caddy + `license.yaml` · Kunde nur Browser |

Erstes Lizenzprodukt = diese Appliance mit **`AIOS-CORE`**. Details: [11-PLATFORM-VM.md](11-PLATFORM-VM.md).

Compose-Schichten darunter sind **VM-agnostisch** (brauchen Docker).

---

## Das Prinzip: Ein Stack, drei Deploy-Schichten

v1 war ein Monolith — alles oder nichts. v2 ist in drei unabhängig deploybare Schichten aufgeteilt:

```
Modus 3 — Full Stack (Fach-Agenten)
  ├── Modus 2 — Core + Platform-Agenten  ← muss vollständig laufen
  │     └── Modus 1 — Core OS (minimal)
  │           └── Infra + LangFuse (immer)
  └── + Fach-Agenten (erst nach Platform-Gate)
```

**Verbindliche Reihenfolge:** Infra → Core → Platform (Gate) → Fach-Agenten.

Jede Schicht ist eigenständig lauffähig und testbar — **Fach-Agenten nur nach bestandenem Platform-Gate** (siehe [ROADMAP.md Kap. 7.0.1](../ROADMAP.md)).

---

## Infra-Basis (immer gestartet)

```bash
docker compose -f deploy/infra.yml -f deploy/monitoring.yml up -d
```

Startet: Qdrant · Letta · Postgres (platform + letta + litellm) · LiteLLM · SearXNG · **LangFuse**

```yaml
# deploy/infra.yml (Kurzform)
services:
  qdrant:       ports: ["6333:6333"]
  letta:        ports: ["8283:8283"]
  postgres-platform: # DB für Orchestrator, Scheduler, Checkpoints, Audit
  postgres-letta:    # Letta intern
  postgres-litellm:  # LiteLLM intern
  litellm:      ports: ["4000:4000"]
  searxng:      ports: ["8888:8888"]
```

---

## Modus 1 — Core OS

**Zweck:** Minimales OS — keine Agenten, kein Memory-Curator, kein Scheduler.  
**Gut für:** Entwicklung, Testing, neuen Tenant anlegen.

```bash
docker compose -f deploy/infra.yml -f deploy/monitoring.yml -f deploy/core.yml up -d
```

**Gestartet:**
| Service | Port | Rolle |
|---------|------|-------|
| orchestrator | 8091 | Intent-Router, Context-Builder, Dispatch, Audit |
| workflow-engine | intern | LangGraph-Wrapper (kein eigener Port, im Orchestrator) |
| skill-service | 8095 | Skill-Loop, Skill-Store |
| search-service | 8094 | **Unified Search** (L1 + G + SK + A) |
| memory-gateway | intern / :4000 | **Memory Gateway** = Inference + Persist-Hook (P19) |
| mcp-gateway | 8097 | Einziger MCP-Konnektivitäts-Layer |
| console-web | 8092 | Next.js UI |
| console-api | 8093 | BFF |
| langfuse | 3000 | **Tracing ab Tag 1** |
| chat-capture | intern | Phase 1b — Gemini/Antigravity → `/v1/chat-import` (`deploy/chat-capture.yml`) |

**Akzeptanztest:**
```bash
curl http://localhost:8091/health        # → {"status":"ok","mode":"core"}
curl http://localhost:8097/v1/servers    # → Liste der nativen MCP-Server
curl http://localhost:8094/v1/search     # → Unified Search
curl http://localhost:8091/v1/models     # → ai-os-sovereign (default)
curl http://localhost:3000/api/public/health  # → LangFuse
curl http://localhost:8092              # → HTML
```

---

## Modus 2 — Core + Platform-Agenten

**Zweck:** Vollständige Plattform mit Memory, Guardrails, Monitor und Scheduler.  
**Gut für:** Produktiver Betrieb, Tenant-Onboarding, tägliche Workflows.

```bash
docker compose \
  -f deploy/infra.yml \
  -f deploy/monitoring.yml \
  -f deploy/core.yml \
  -f deploy/platform-agents.yml \
  up -d
```

**Zusätzlich gestartet:**
| Service | Rolle |
|---------|-------|
| pipeline-agent | RAG-Pipeline (7-Schritt) |
| ingest-worker | Inbox-Polling → Qdrant-Indexierung |
| memory-agent | L1/L2/L3-Curators (Cron) |
| guardrails-agent | Policy-Enforcement, PII-Scan |
| monitor-agent | Services + Audit + FinOps |
| scheduler-agent | Cron-Runner + Job-Store |

**Tenant-Bootstrap nach erstem Start:**
```bash
python -m core.orchestrator.bootstrap --tenant nextchapter
# → Qdrant-Namespace anlegen
# → Letta-Projekt anlegen
# → KG-Root-Knoten erstellen
# → Seed-Knowledge indexieren
# → LiteLLM-Budget einrichten
```

**Akzeptanztest:**
```bash
# daily-briefing Workflow ausführen
curl -X POST http://localhost:8091/v1/dispatch \
  -H 'Content-Type: application/json' \
  -d '{"intent":"daily-briefing","tenant_id":"nextchapter"}'
# → {"status":"queued","workflow_run_id":"..."}

# Scheduler-Jobs anzeigen
curl http://localhost:8091/v1/scheduler/jobs?tenant_id=nextchapter
```

---

## Modus 3 — Full Stack (Core + Platform + Fach-Agenten)

**Zweck:** Vollständiger Stack mit installierten Fach-Agenten — **nur nach Platform-Gate**.

```bash
# Platform-Gate muss PASS sein
python -m tests.platform_gate --tenant platform-test

# Beispiel: nextchapter mit research + blog + email
docker compose \
  -f deploy/infra.yml \
  -f deploy/monitoring.yml \
  -f deploy/core.yml \
  -f deploy/platform-agents.yml \
  -f deploy/agents/research.yml \
  -f deploy/agents/blog.yml \
  -f deploy/agents/email.yml \
  up -d
```

**Fach-Agenten-Compose-Files:**
```yaml
# deploy/agents/research.yml
services:
  research-agent:
    build: ./agents/research
    environment:
      TENANT_ID: ${DEFAULT_TENANT}
      ORCHESTRATOR_URL: http://orchestrator:8091
      MCP_GATEWAY_URL: http://mcp-gateway:8097
    depends_on: [orchestrator, mcp-gateway]
```

**Pakete installieren/deinstallieren:**
```bash
# Paket für Tenant aktivieren
python -m core.packages install --tenant nextchapter --package research-agent

# Paket deaktivieren (Container läuft weiter, Tenant hat keinen Zugriff)
python -m core.packages uninstall --tenant nextchapter --package email-agent

# Status anzeigen
python -m core.packages status --tenant nextchapter
```

---

## Externaler MCP-Sidecar (M2)

Für externe MCP-Server (GitHub, Google Calendar etc.) werden Sidecar-Container gestartet:

```bash
docker compose \
  -f deploy/infra.yml \
  -f deploy/core.yml \
  -f deploy/mcp-external.yml \  # GitHub + Calendar Sidecars
  up -d
```

```yaml
# deploy/mcp-external.yml
services:
  mcp-github:
    image: ghcr.io/github/github-mcp-server:latest
    environment:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    networks: [aios-internal]

  mcp-calendar:
    image: ghcr.io/modelcontextprotocol/google-calendar:latest
    environment:
      GOOGLE_CREDENTIALS_JSON: ${GOOGLE_CREDENTIALS_JSON}
    networks: [aios-internal]
```

---

## Umgebungsvariablen (.env)

```env
# === Inference ===
OLLAMA_HOST=192.168.178.116
OLLAMA_PORT=11434
OLLAMA_DEFAULT_MODEL=qwen3.6-64k:latest
DEFAULT_COMPUTE_MODE=sovereign         # sovereign | balanced | premium
# Cloud — ausschließlich OpenRouter
OPENROUTER_API_KEY=

# === LangFuse (Pflicht ab Tag 1) ===
LANGFUSE_HOST=http://langfuse:3000
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_PG_PW=

# === Datenbanken ===
POSTGRES_PASSWORD=sicheres_passwort_hier
LETTA_POSTGRES_PASSWORD=letta_passwort

# === Services ===
ORCHESTRATOR_PORT=8091
CONSOLE_PORT=8092
CONSOLE_API_PORT=8093
MCP_GATEWAY_PORT=8097
SKILL_SERVICE_PORT=8095
SCHEDULER_PORT=8096

# === Tenant ===
DEFAULT_TENANT=nextchapter

# === Externe MCP-Sidecars (Phase 6) ===
GITHUB_TOKEN=
GOOGLE_CREDENTIALS_JSON=

# === FinOps ===
LITELLM_MONTHLY_BUDGET_USD=50
LITELLM_ALERT_AT_PCT=80
```

---

## Host-Skript (~/ai-os.sh Äquivalent)

```bash
#!/bin/bash
# ~/ai-os-v2.sh — Host-CLI für AI-OS v2

COMPOSE_BASE="docker compose -f deploy/infra.yml"

case $1 in
  start)    $COMPOSE_BASE -f deploy/core.yml -f deploy/platform-agents.yml up -d ;;
  stop)     $COMPOSE_BASE down ;;
  status)   docker compose ps ;;
  console)  open http://localhost:8092 ;;
  logs)     docker compose logs -f ${2:-orchestrator} ;;
  bootstrap) python -m core.orchestrator.bootstrap --tenant ${2:-nextchapter} ;;
  test)     python -m pytest tests/ -v ;;
  shell)    docker exec -it ai-os-v2-orchestrator-1 bash ;;
  *)        echo "Befehle: start | stop | status | console | logs | bootstrap | test | shell" ;;
esac
```

---

## Port-Übersicht

| Port | Service | Zugriff |
|------|---------|---------|
| 8091 | Orchestrator | intern (Console-API) |
| 8092 | Console (Next.js) | Browser |
| 8093 | Console-API (BFF) | Console-Web |
| 8094 | Search-Service (Unified Search) | intern (Console, Agenten) |
| 8095 | Skill-Service | intern (Orchestrator) |
| 8096 | Scheduler | intern (Orchestrator) |
| 8097 | MCP-Gateway | intern (Agenten) |
| 3000 | LangFuse | intern (Browser optional) |
| 4000 | LiteLLM | intern (Agenten) |
| 6333 | Qdrant HTTP | intern |
| 6335 | Qdrant GRPC | intern |
| 8283 | Letta API | intern |
| 8888 | SearXNG | intern (MCP web_search) |

Alle Services außer Console (8092) sind **nur intern erreichbar** — kein Expose nach außen.
