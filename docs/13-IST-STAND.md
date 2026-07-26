# AI-OS v2 — Ist-Stand

**Stand:** 2026-07-26 (Platform Gate ✅ + PII Redactor ✅ + Async 6-Slice Context Bundle ✅ + LangGraph Checkpointing ✅ + Master Testsuite ✅) · **Repo:** [NextChapterExperts/ai-os-v2](https://github.com/NextChapterExperts/ai-os-v2)  
**Zweck:** Was heute **wirklich läuft** vs. was in Roadmap/Architektur als **Ziel** spezifiziert ist.  
**Ziel-Spec bleibt:** [ROADMAP.md](../ROADMAP.md) · [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) · [14-KONTEXT.md](14-KONTEXT.md) — dieses Dokument überschreibt die Vision nicht, sondern den Fortschritt.

---

## Kurzfazit

Auf der **NCE DEV-VM** läuft ein **gehärtetes Phase-0/1/2-Fundament** für das KI-Betriebssystem:
- **Automatisierte Master-Testsuite (`./scripts/run-all-tests.sh`):** 63 Pytest-Tests, 19 Memory-Testfälle und 7 Compute-Mode-Testfälle durchlaufen zu 100% fehlerfrei.
- **Automatisierte Platform-Gate Suite (`tests/test_platform_gate.py`):** Prüft vor jedem Fach-Agenten-Deployment 5 Sicherheits- & Vertragsschranken (P10).
- **PII-Redaction-Gateway (`core/orchestrator/pii_redactor.py`):** Maskiert E-Mails, Telefonnummern, IP-Adressen und IBANs vor Cloud-Escalations und stellt sie nach der Antwort verlustfrei wieder her (P12/P15).
- **Asynchrone 6-Slice Context Bundle Engine (`context_resolution.py`):** Löst L0 Schema, L1 Search, G Graph, L2/L3 Memory, SK Skill und State parallel unter 50ms mit TTL-Caching auf (P1/P13).
- **LangGraph Checkpointing & Resume (`core/workflow_engine/`):** Zustandsspeicherung in Postgres `workflow_checkpoints` (mit SQLite-Fallback) sowie Endpoints `/v1/workflow/checkpoint/{thread_id}` und `/v1/workflow/resume` (P7).
- **Härtung & Sicherheit:** Path-Traversal-Schutz, Subprozess-Timeouts (30s) in `watcher.py`, atomares File-Locking (`fcntl.flock`) in `run_distill.py` und `asyncio.to_thread`-Wrapping für blockierende I/O-Endpoints.

---

## Phasen-Fortschritt

| Phase | Thema | Status |
|-------|--------|--------|
| **0** | Infra + LangFuse + DB-Schema + DEV-VM-Bootstrap + Repo | **Erledigt** |
| **1** | Core OS + Memory Gateway + Unified Search + Context Bundle Engine | **Erledigt** (Asynchrone 6-Slice Engine <50ms ✅; Compute-Modi Switcher ✅; Memory Gateway Persist-Hook ✅ `core/memory_gateway/` + `GET /v1/models` + `POST /v1/chat/completions`) |
| **1b** | Chat Capture | **weitgehend erledigt** (Cursor ✅; Antigravity-Poller ✅; Gemini-Inbox ✅; Console `/platform/capture` ✅) |
| **2** | Platform-Agenten + Platform-Gate | **weitgehend erledigt** (Platform-Gate Suite `tests/test_platform_gate.py` ✅; Company-Brain-DP-Commit + KG für `org:*` steht; PII Redactor ✅; LangGraph Checkpointing ✅) |
| **3** | Agent-SDK | **bereit zur Anbindung** |
| **4** | Fach-Agenten | **freigegeben** (Platform-Gate grün) |
| **5** | Console vollständig | **Skeleton** (3 Routen) |
| **6** | Multi-Tenant Runtime + GraphRAG | **in Vorbereitung** |

Zusätzlich (nicht als eigene Roadmap-Phase, aber gebaut): **Offering vs Engagement** — Seed + Packs + Intent `daily_open_loops`.
Zusätzlich: **File-Ingest-Watcher** (Rohdatei-Suche über `Projekte/active/`, Bridge bis Fach-Agenten stehen — [ADR 0002](adr/0002-file-ingest-watcher-und-rolle-von-cursor.md)).
Zusätzlich: **Unified Search** (`unified_search`-Intent, foederiert Graph + `content` + `raw-files` via Query-Router, Console-Seite `/search`).
Zusätzlich: **Ingest-Agent + Knowledge Graph** — `core/ingest_agent/` committet Company-Brain-Seed als `org:*`-DataProducts über `POST /v1/dataproduct/commit` in `kg_nodes`/`kg_edges` (Postgres) + Audit-Hash-Chain (`ai_os_log`); published `OrgKnowledgeAsset`s zusätzlich in Qdrant `content`. Details: [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md), [03-DATENPRODUKTE.md](03-DATENPRODUKTE.md).
Zusätzlich: **Graph-Suche + Query-Router + Console-UI** — `core/orchestrator/kg_search.py`, `query_router.py`, Console `/platform/kg`.
Zusätzlich: **L2-Curator** — `core/memory/l2_curator.py` verdichtet SQLite-Chunks (24h) zu Tagesdigest in Letta L2; **L3-Curator** extrahiert Fakten → `org:Claim`. **L1-Curator** — Qdrant `content` Stats/Dedup/Rolling 90d. **Working/Tactical-Memory** — flüchtiger Run-State, Destillation am Dispatch-Ende (P9). APIs: `POST /v1/memory/curate/l1|l2|l3`, `GET /v1/memory/l1/stats`.

---

## Was läuft (DEV-VM)

### Services / Prozesse

| Komponente | Port / Pfad | Start | Status |
|------------|-------------|-------|--------|
| **Console** `core/console-web` (`core/console` → Symlink) | `:8092` | `cd core/console-web && npm run dev` | Lagebild + Dispatch, `/platform` Health, `/workflows` Platzhalter |
| **Orchestrator** | `:8091` | `./core/orchestrator/run.sh` | FastAPI: `/health`, `POST /v1/dispatch`, **`GET /v1/models`**, **`POST /v1/chat/completions`** (Memory Gateway), Brain-Listen, DP-Commit, KG-API |
| **MCP-Gateway** | `:8097` | `./core/mcp_gateway/run.sh` | Allowlist + Mail/Calendar-**Stubs** (nicht in Compose) |
| **Cursor Capture** | systemd user / `npm start` | `core/capture/` | Pollt Cursor-Transkripte → `/opt/ai-os/memory/memory.db` |
| **Antigravity Capture** | systemd user | `core/capture/antigravity-job.mjs` | Pollt `~/.gemini/antigravity/brain` → `POST /v1/chat-import` |
| **Gemini-Inbox Capture** | systemd user | `core/capture/gemini-inbox-job.mjs` | Pollt `/opt/ai-os/ingest/inbox/{gemini,chats}/` → chat-import |
| **File-Ingest-Watcher** | systemd user | `core/file_ingest_watcher/` | Scannt `Projekte/active/**`, embedded lokal → Qdrant-Collection `raw-files` (Bridge, siehe [ADR 0002](adr/0002-file-ingest-watcher-und-rolle-von-cursor.md)) |
| **Ingest-Agent** | systemd user Timer (täglich 03:30) | `core/ingest_agent/` | Company-Brain-Seed → DP-Commit (KG) + Qdrant `content` |
| **Compose Infra** | diverse | `docker compose -f deploy/infra.yml -f deploy/monitoring.yml up -d` | Qdrant, Postgres (Host-Port `127.0.0.1:5432`), LiteLLM, SearXNG, Letta (SQLite), LangFuse |

### Orchestrator-Intents (heute)

| Intent | Verhalten |
|--------|-----------|
| `ping` | Health |
| `daily_open_loops` | Engagements + Seed-Meetings + Mail-Stub-Actions → kurze Tageslage |
| `memory_ask` | Zeitfenster aus Frage (`resolve_window`) + Letta L2 Archival (Fallback SQLite) + Ollama-Summary |
| `mail_triage` | Stub über MCP-Client |
| `unified_search` | Query-Router (§12.1): Graph, Qdrant, **Letta episodisch** (`source_type: episodic`) oder SQLite-Fallback |

Lagebild-Feld in der Console → `POST /api/dispatch` → Orchestrator. Suche: Console-Seite `/search` (foederiert) und `/platform/kg` (Graph-Browser mit Node-Detail).

### Company Brain / Knowledge Graph (heute)

- Seed: `customers/nextchapter/knowledge/seed/{00..08}-*.md` + `brain.json` (Organization, Offerings, People, Partners, Policies, Decisions, KnowledgeAssets)
- Schema: `packages/org-brain/schema/{entities,edges}.yaml` (L0, dokumentarisch — Validierung faktisch über `core/orchestrator/dataproducts.py`)
- Graph: Postgres `kg_nodes`/`kg_edges` (`config/init-platform.sql`), Commit nur über `POST /v1/dataproduct/commit` (`core/orchestrator/dp_service.py`) — nie Direktzugriff aus Agenten
- Audit: `ai_os_log` mit Hash-Chain (P17) pro DP-Commit
- Stand: **58 Nodes**, **37 Edges** (`org:Organization` 9, `org:Person` 1, `org:Offering` 5, `org:Engagement` 12, `org:Policy` 4, `org:Decision` 4, `org:KnowledgeAsset` 23) — erfüllt DoD aus [09-COMPANY-BRAIN.md §7](09-COMPANY-BRAIN.md) (≥10 Nodes, ≥5 Edges); 5 Abnahmefragen aus §8 getestet, siehe dort
- `org:Meeting` / `org:Claim`: Commit-Mapping fertig; **org:Claim** wird vom **L3-Curator** befüllt (`core/memory/l3_curator.py` → DP-Commit). `org:Meeting` noch ohne Calendar-MCP
- Packs: `packages/offerings/{sap-apim-training,studenten-beratung}/` (Seed + LICENSE, Skills/Workflows noch README-Stubs)
- Delivery-Hinweis: `deploy/profiles/delivery.yml`

### Memory-Pfade (faktisch)

| Pfad | Nutzung |
|------|---------|
| `/opt/ai-os/memory/memory.db` | Capture + Console-Suche + `memory_ask` |
| `/opt/ai-os/memory/state/` | Capture-State, Orchestrator-Audit-JSONL, **`letta-agents.json`** (tenant → agent_id) |
| `/opt/ai-os/ingest/inbox` | vorbereitet, noch leer |
| `AIOS_MEMORY_PROJECT=…` | Projektfilter für Memory — Slug haengt vom Cursor-Workspace-Root ab (`core/capture/cursor-job.mjs`) und aendert sich mit ihm; aktuell `home-peter-Projekte` |

Inference-Default: Ollama LAN (`OLLAMA_HOST` / `OLLAMA_DEFAULT_MODEL` in `.env`) — **kein** API-Secret nötig für sovereign.

---

## Stubs / Teilimplementierung

- MCP Mail/Calendar: deterministische Stubs, keine echten IMAP/CalDAV-Calls
- Meeting-Teilnehmer (`/v1/meetings/participants/*`): Orchestrator-Bridge — **Übergang** bis **comms-manager-agent** (Phase 4, MCP-only); siehe [ROADMAP §9.4](../ROADMAP.md#94-kommunikationsmanager-agent-comms-manager-agent)
- Context Bundle: Slice-Struktur vorhanden; Retrieval/Graph/Skills noch Notes
- Console `/workflows`: UI „geplant“, kein Scheduler/LangGraph
- Letta in Compose: läuft mit SQLite-Volume; **L2 Archival angebunden** (`letta_client.py`, Agent pro Tenant, Ollama-Embeddings via LAN-IP)
- Appliance `image-build.sh` / cloud-init: Scaffold, kein produktionsreifes Image
- `deploy/core.yml`: Orchestrator optional unter Profile `core-docker`; Console/Capture/MCP nicht als Compose-Services

---

## Noch geplant (im Repo fehlend oder nur spezifiziert)

- `sdk/`, `tests/`, `platform-agents/`, `agents/`
- `deploy/platform-agents.yml`, `deploy/agents/*`, `deploy/chat-capture.yml`
- Services: console-api `:8093`, search `:8094` (dediziert, aktuell Teil des Orchestrators), skill `:8095`, scheduler `:8096`
- Memory Gateway Persist-Hook ✅ — LangGraph, `POST /v1/compute/mode`, Auto-Router/CAG offen
- L2-Curator ✅ (täglich 02:00, `scripts/run-l2-curator.py`) — L3 ✅
- Skill-Store (SK) — `query_router.py` kennt `use_sk`, aber `core/skills/` existiert noch nicht
- Platform-Gate (`python -m tests.platform_gate`)
- Gemini/Antigravity Capture ✅ (Poller + `/v1/chat-import` + Console `/platform/capture`); ChatGPT-Export + Drive-Poller offen
- Console `/platform/kg`: Decision-Inbox (Human-Gate für Claims) fehlt noch — Graph-Browse/Suche/Detail ist da

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
