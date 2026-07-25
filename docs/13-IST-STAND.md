# AI-OS v2 — Ist-Stand

**Stand:** 2026-07-25 · **Repo:** [NextChapterExperts/ai-os-v2](https://github.com/NextChapterExperts/ai-os-v2)  
**Zweck:** Was heute **wirklich läuft** vs. was in Roadmap/Architektur als **Ziel** spezifiziert ist.  
**Ziel-Spec bleibt:** [ROADMAP.md](../ROADMAP.md) · [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) — dieses Dokument überschreibt die Vision nicht, sondern den Fortschritt.

---

## Kurzfazit

Auf der **NCE DEV-VM** läuft ein **Phase-0/1-Skeleton** plus ein **Phase-2-Vorgriff** auf den Company Brain: Infra (Compose), Console, Orchestrator, MCP-Gateway-Stubs, Cursor→SQLite-Capture, Unified Search (`content` + `raw-files` + jetzt **Graph**), Knowledge Graph (`kg_nodes`/`kg_edges`) mit DP-Commit für `org:*`, Query-Router (§12.1) und Console-UI `/platform/kg`.  
**Noch nicht:** Skill-Store, LangGraph, Platform-Agenten-Laufzeit, SDK, Platform-Gate, echte MCP-Adapter, Appliance-Image-Build. **Memory L1+L2+L3-Curator** ✅ (Claims → KG, Profil → Letta Core).

---

## Phasen-Fortschritt

| Phase | Thema | Status |
|-------|--------|--------|
| **0** | Infra + LangFuse + DB-Schema + DEV-VM-Bootstrap + Repo | **weitgehend erledigt** |
| **1** | Core OS + Memory Gateway + Unified Search | **teilweise** (Memory Gateway Persist-Hook ✅ `core/memory_gateway/` + `GET /v1/models` + `POST /v1/chat/completions`; Orch/Console/MCP + Unified Search + Graph + Query-Router; LangGraph + `POST /v1/compute/mode` fehlen) |
| **1b** | Chat Capture | **teilweise** (Cursor ✅; Antigravity-Poller ✅; Gemini-Inbox ✅; Console `/platform/capture` ✅; ChatGPT-Export + Drive-Poller ⏳) |
| **2** | Platform-Agenten + Platform-Gate | **teilweise** (Company-Brain-DP-Commit + KG für `org:*` steht; Platform-Agenten-Laufzeit/Gate selbst offen) |
| **3** | Agent-SDK | **offen** |
| **4** | Fach-Agenten | **gesperrt** (vor Gate) |
| **5** | Console vollständig | **Skeleton** (3 Routen) |
| **6** | Multi-Tenant Runtime + GraphRAG | **offen** |

Zusätzlich (nicht als eigene Roadmap-Phase, aber gebaut): **Offering vs Engagement** — Seed + Packs + Intent `daily_open_loops`.
Zusätzlich: **File-Ingest-Watcher** (Rohdatei-Suche über `Projekte/active/`, Bridge bis Fach-Agenten stehen — [ADR 0002](adr/0002-file-ingest-watcher-und-rolle-von-cursor.md)).
Zusätzlich: **Unified Search** (`unified_search`-Intent, foederiert Graph + `content` + `raw-files` via Query-Router, Console-Seite `/search`).
Zusätzlich: **Ingest-Agent + Knowledge Graph** — `core/ingest_agent/` committet Company-Brain-Seed als `org:*`-DataProducts über `POST /v1/dataproduct/commit` in `kg_nodes`/`kg_edges` (Postgres) + Audit-Hash-Chain (`ai_os_log`); published `OrgKnowledgeAsset`s zusätzlich in Qdrant `content`. Details: [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md), [03-DATENPRODUKTE.md](03-DATENPRODUKTE.md).
Zusätzlich: **Graph-Suche + Query-Router + Console-UI** — `core/orchestrator/kg_search.py`, `query_router.py`, Console `/platform/kg`.
Zusätzlich: **L2-Curator** — `core/memory/l2_curator.py` verdichtet SQLite-Chunks (24h) zu Tagesdigest in Letta L2; **L3-Curator** extrahiert Fakten → `org:Claim`. APIs: `POST /v1/memory/curate/l2|l3`.

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
