# AI-OS v2 — Ist-Stand

**Stand:** 2026-07-24 · **Repo:** [NextChapterExperts/ai-os-v2](https://github.com/NextChapterExperts/ai-os-v2)  
**Zweck:** Was heute **wirklich läuft** vs. was in Roadmap/Architektur als **Ziel** spezifiziert ist.  
**Ziel-Spec bleibt:** [ROADMAP.md](../ROADMAP.md) · [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) — dieses Dokument überschreibt die Vision nicht, sondern den Fortschritt.

---

## Kurzfazit

Auf der **NCE DEV-VM** läuft ein **Phase-0/1-Skeleton**: Infra (Compose), Console, Orchestrator, MCP-Gateway-Stubs, Cursor→SQLite-Capture, Company-Brain-Seed (Offerings/Engagements).  
**Noch nicht:** Unified Search, Memory Gateway (Persist-Hook), LangGraph, Platform-Agenten, SDK, Platform-Gate, echte MCP-Adapter, Appliance-Image-Build.

---

## Phasen-Fortschritt

| Phase | Thema | Status |
|-------|--------|--------|
| **0** | Infra + LangFuse + DB-Schema + DEV-VM-Bootstrap + Repo | **weitgehend erledigt** |
| **1** | Core OS + Memory Gateway + Unified Search | **Skeleton** (Orch/Console/MCP; Search/Gateway fehlen) |
| **1b** | Chat Capture | **teilweise** (Cursor→SQLite; Gemini/Antigravity/UI fehlen) |
| **2** | Platform-Agenten + Platform-Gate | **offen** |
| **3** | Agent-SDK | **offen** |
| **4** | Fach-Agenten | **gesperrt** (vor Gate) |
| **5** | Console vollständig | **Skeleton** (3 Routen) |
| **6** | Multi-Tenant Runtime + GraphRAG | **offen** |

Zusätzlich (nicht als eigene Roadmap-Phase, aber gebaut): **Offering vs Engagement** — Seed + Packs + Intent `daily_open_loops`.
Zusätzlich: **File-Ingest-Watcher** (Rohdatei-Suche über `Projekte/active/`, Bridge bis Fach-Agenten stehen — [ADR 0002](adr/0002-file-ingest-watcher-und-rolle-von-cursor.md)).

---

## Was läuft (DEV-VM)

### Services / Prozesse

| Komponente | Port / Pfad | Start | Status |
|------------|-------------|-------|--------|
| **Console** `core/console-web` (`core/console` → Symlink) | `:8092` | `cd core/console-web && npm run dev` | Lagebild + Dispatch, `/platform` Health, `/workflows` Platzhalter |
| **Orchestrator** | `:8091` | `./core/orchestrator/run.sh` | FastAPI: `/health`, `POST /v1/dispatch`, Brain-Listen |
| **MCP-Gateway** | `:8097` | `./core/mcp_gateway/run.sh` | Allowlist + Mail/Calendar-**Stubs** (nicht in Compose) |
| **Cursor Capture** | systemd user / `npm start` | `core/capture/` | Pollt Cursor-Transkripte → `/opt/ai-os/memory/memory.db` |
| **File-Ingest-Watcher** | systemd user | `core/file_ingest_watcher/` | Scannt `Projekte/active/**`, embedded lokal → Qdrant-Collection `raw-files` (Bridge, siehe [ADR 0002](adr/0002-file-ingest-watcher-und-rolle-von-cursor.md)) |
| **Compose Infra** | diverse | `docker compose -f deploy/infra.yml -f deploy/monitoring.yml up -d` | Qdrant, Postgres, LiteLLM, SearXNG, Letta (SQLite), LangFuse |

### Orchestrator-Intents (heute)

| Intent | Verhalten |
|--------|-----------|
| `ping` | Health |
| `daily_open_loops` | Engagements + Seed-Meetings + Mail-Stub-Actions → kurze Tageslage |
| `memory_ask` | SQLite-FTS + Ollama (LAN) |
| `mail_triage` | Stub über MCP-Client |

Lagebild-Feld in der Console → `POST /api/dispatch` → Orchestrator.

### Company Brain / Offerings (heute)

- Seed: `customers/nextchapter/knowledge/seed/brain.json` (Offerings, Engagements, Meetings, Orgs)
- Packs: `packages/offerings/{sap-apim-training,studenten-beratung}/` (Seed + LICENSE, Skills/Workflows noch README-Stubs)
- Delivery-Hinweis: `deploy/profiles/delivery.yml`

### Memory-Pfade (faktisch)

| Pfad | Nutzung |
|------|---------|
| `/opt/ai-os/memory/memory.db` | Capture + Console-Suche + `memory_ask` |
| `/opt/ai-os/memory/state/` | Capture-State, Orchestrator-Audit-JSONL |
| `/opt/ai-os/ingest/inbox` | vorbereitet, noch leer |
| `AIOS_MEMORY_PROJECT=…` | Projektfilter für Memory |

Inference-Default: Ollama LAN (`OLLAMA_HOST` / `OLLAMA_DEFAULT_MODEL` in `.env`) — **kein** API-Secret nötig für sovereign.

---

## Stubs / Teilimplementierung

- MCP Mail/Calendar: deterministische Stubs, keine echten IMAP/CalDAV-Calls
- Context Bundle: Slice-Struktur vorhanden; Retrieval/Graph/Skills noch Notes
- Console `/workflows`: UI „geplant“, kein Scheduler/LangGraph
- Letta in Compose: läuft mit SQLite-Volume (Postgres-Pfad problematisch)
- Appliance `image-build.sh` / cloud-init: Scaffold, kein produktionsreifes Image
- `deploy/core.yml`: Orchestrator optional unter Profile `core-docker`; Console/Capture/MCP nicht als Compose-Services

---

## Noch geplant (im Repo fehlend oder nur spezifiziert)

- `sdk/`, `tests/`, `platform-agents/`, `agents/`, `packages/org-brain/`
- `deploy/platform-agents.yml`, `deploy/agents/*`, `deploy/chat-capture.yml`
- Services: console-api `:8093`, search `:8094`, skill `:8095`, scheduler `:8096`
- Memory Gateway Persist-Hook, Unified Search, LangGraph, Hash-Audit in Postgres
- Platform-Gate (`python -m tests.platform_gate`)
- Gemini/Antigravity Capture + Console „Chat-Erfassung“

---

## Verifizierter Smoke-Pfad (DEV)

```bash
# 1) Infra (einmal)
docker compose -f deploy/infra.yml -f deploy/monitoring.yml up -d

# 2) Core-Prozesse
./core/orchestrator/run.sh          # :8091
./core/mcp_gateway/run.sh           # :8097
cd core/console-web && npm run dev  # :8092

# 3) Lagebild
# Browser → http://localhost:8092
# Frage z. B. „Was muss ich heute noch machen?“ → Intent daily_open_loops
```

---

## Doku-Lesereihenfolge

| Wenn du … | Lies zuerst |
|-----------|-------------|
| … wissen willst, was **jetzt** geht | **dieses Dokument** |
| … bauen willst (Ziel-Spec) | [ROADMAP.md](../ROADMAP.md) |
| … Architektur-Zielbild brauchst | [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) |
| … deployen willst (Ist + Ziel-Modi) | [04-DEPLOYMENT.md](04-DEPLOYMENT.md) |
| … Console-IA verstehst | [05-CONSOLE-IA.md](05-CONSOLE-IA.md) + Ist unten in Console-Abschnitt |
| … Produkt/VM meinst | [11-PLATFORM-VM.md](11-PLATFORM-VM.md) |
