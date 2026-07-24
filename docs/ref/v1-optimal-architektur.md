# AI-OS — Optimale Ziel-Architektur

**Stand:** Juli 2026 · **Nr. 19** · **Autor:** Peter / NCE  
**Status:** Architektur-Idee / Nordstern — nicht aktueller Ist-Stand  
**Verwandte Dokumente:** [00-VISION.md](00-VISION.md) · [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) · [18-FRAMEWORK-VERGLEICH.md](18-FRAMEWORK-VERGLEICH.md) · [ROADMAP.md](../../ROADMAP.md)

---

## Leitgedanke

Der aktuelle AI-OS-Stack ist ein funktionierender Pilot (~75 % Produktionsreife). Dieses Dokument beschreibt die **optimale Ziel-Architektur** — was AI-OS sein sollte, wenn alle heutigen Baustellen geschlossen und die Erkenntnisse aus dem Framework-Vergleich integriert sind.

**Drei Leitprinzipien bleiben unverändert aus der Vision:**
1. **Determinismus in der Hülle** — Dispatch, Audit, Guardrails, FinOps werden nicht dem LLM überlassen.
2. **Graph vor reinem RAG** — Beziehungen brauchen `G`, nicht nur Vektoren.
3. **MCP als einzige Konnektivitäts-Schnittstelle** — keine ad-hoc-Skript-Verdrahtung.

**Neue Prinzipien aus dem Framework-Vergleich:**
4. **Skill-Loop statt statischer Skripte** — Agenten destillieren ihr Vorgehen als versionierbare Markdown-Skills; kein Wissen geht beim Neustart verloren.
5. **Orchestrierung als State-Machine** — Workflows sind explizite Graphen mit Checkpoints, Retry und Human-in-the-Loop — kein implizites «Agent macht weiter».
6. **A2A als Inter-Agent-Protokoll** — interne Agenten kommunizieren standardisiert; kein proprietäres RPC.

---

## Gesamtbild (Schichten)

```
╔══════════════════════════════════════════════════════════════════╗
║  SCHICHT 0 — HOST                                                ║
║  Cursor IDE · Browser · ~/ai-os.sh · Werkstatt-Queue            ║
╚══════════════════════╦═══════════════════════════════════════════╝
                       ║ Incus-Proxy
╔══════════════════════╩═══════════════════════════════════════════╗
║  SCHICHT 1 — CONSOLE (Mensch-Maschine-Grenze)                   ║
║                                                                  ║
║  console-web (Next.js :8092)   console-api (BFF :8093)          ║
║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   ║
║  │ Lagebild │ │Briefing  │ │ Research │ │  Content Factory │   ║
║  │ Monitor  │ │ Email    │ │ Chat-Cap │ │  Werkstatt-Sync  │   ║
║  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   ║
╚══════════════════════╦═══════════════════════════════════════════╝
                       ║ JSON / MCP
╔══════════════════════╩═══════════════════════════════════════════╗
║  SCHICHT 2 — ORCHESTRATOR (OS-Kernel :8091)                     ║
║                                                                  ║
║  Intent-Router → Context-Builder → Workflow-Engine → Audit      ║
║  (deterministische Python-Hülle — kein LLM-Dispatch)            ║
╚══════╦═══════╦═════════╦══════════╦═════════╦════════════════════╝
       ║       ║         ║          ║         ║
╔══════╩╗  ╔══╩═══╗  ╔══╩══╗  ╔════╩═╗  ╔════╩═════════════════╗
║ MCP   ║  ║Work- ║  ║Skill║  ║Sched-║  ║  Platform-Agenten   ║
║ Gate- ║  ║flow- ║  ║-Loop║  ║uler  ║  ║  (Pipeline, Ingest, ║
║ way   ║  ║Engine║  ║     ║  ║Agent ║  ║   Memory, Guards,   ║
║ (M2+) ║  ║(Lang-║  ║(neu)║  ║(neu) ║  ║   Monitor, Chat,    ║
║       ║  ║Graph)║  ║     ║  ║      ║  ║   Code)             ║
╚══════╦╝  ╚══════╝  ╚═════╝  ╚══════╝  ╚═════════════════════╝
       ║
╔══════╩══════════════════════════════════════════════════════════╗
║  SCHICHT 3 — MCP-SERVER (native + extern)                       ║
║                                                                  ║
║  mail · calendar · cms · drive · web · kg · memory · qdrant     ║
║  github · vercel · sap · slack · …(M2/M3 extern)               ║
╚══════════════════════════════════════════════════════════════════╝
                       ║
╔══════════════════════╩═══════════════════════════════════════════╗
║  SCHICHT 4 — DATENSCHICHT (souverän, lokal)                     ║
║                                                                  ║
║  Qdrant (L1) · Letta/Postgres (L2/L3) · Knowledge Graph (Neo4j) ║
║  LiteLLM-Router · Pipeline-Log · Guardrails-DB                  ║
╚══════════════════════════════════════════════════════════════════╝
                       ║
╔══════════════════════╩═══════════════════════════════════════════╗
║  SCHICHT 5 — INFERENCE                                           ║
║                                                                  ║
║  Ollama (LAN :11434) · extern (OpenRouter / Anthropic / OpenAI) ║
║  LiteLLM als einziger Einstiegspunkt — Modell-agnostisch        ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Die 7 Kernkomponenten im Detail

### K1 — Orchestrator (deterministische Hülle)

**Was er tut:**  
Empfängt jeden Intent (von Console, CLI, Cron, Agent), baut ein **Context Bundle** (CTX1–CTX5), routet an den zuständigen Workflow oder Agenten, schreibt jeden Schritt in den Audit-Log.

**Optimal:**
- Intent-Klassifikation: regelbasiert + LLM-Fallback (nicht reines LLM-Dispatch)
- Context Bundle CTX1–CTX5 vollständig (aktuell offen: CTX4 Debug-Kontext)
- **A2A-Protokoll** für Agent-zu-Agent-Kommunikation (statt proprietärem RPC)
- Jeder Workflow-Aufruf ist idempotent und replaybar

```
Intent → Intent-Router
          ├── Einfach (Lookup, Q&A) → Context Bundle → LLM-Call → Audit
          ├── Komplex → Workflow-Engine → [Steps] → Audit
          └── Unbekannt → Human-in-the-Loop → Skill-Destillation
```

---

### K2 — Workflow-Engine (LangGraph-basiert)

**Warum LangGraph statt eigener Lösung:**  
AI-OS's Workflow-Runner ist ein funktionierender Prototyp. LangGraph gibt Checkpointing, Retry-Graphen, parallele Branches und Human-in-the-Loop-Breakpoints als bewiesene Production-Infrastruktur — kein Grund, das selbst zu bauen.

**Optimal:**
- LangGraph als Engine unter dem bestehenden `workflow_runner.py`-Interface
- Alle bestehenden Workflow-Definitionen (daily-briefing, research, blog-pipeline) als LangGraph-Graphen
- Checkpoint-Store: Postgres (bereits vorhanden)
- LangSmith-Tracing optional für Debug-Sessions
- `interrupt()`-Primitive für Benutzer-Freigaben (z. B. vor Blog-Publish)

```python
# Konzept: Workflow als LangGraph
from langgraph.graph import StateGraph

graph = StateGraph(BlogState)
graph.add_node("research", research_node)
graph.add_node("draft", draft_node)
graph.add_node("compliance", compliance_node)
graph.add_node("review", interrupt_node)   # Human-in-the-Loop
graph.add_node("publish", publish_node)
graph.add_edge("research", "draft")
graph.add_edge("draft", "compliance")
graph.add_conditional_edges("compliance", route_on_compliance)
# Checkpoint in Postgres — replaybar
```

---

### K3 — Skill-Loop (Hermes-Muster)

**Die größte Lücke im aktuellen AI-OS.**

**Wie es funktioniert:**
1. Agent löst komplexen Task.
2. Nach Abschluss: LLM destilliert den Ablauf als Markdown-Skill-Dokument.
3. Skill wird in Qdrant (Vektor) + FTS5 (Volltext) indiziert.
4. Bei künftigen ähnlichen Tasks: Skill wird in den Context Bundle geladen.
5. Nach jeder Wiederholung: Skill-Dokument wird verfeinert (nicht ersetzt).

**Optimal — Skill-Dokument-Format:**

```markdown
---
id: blog-publish-compliance-check
title: Blog-Artikel auf Compliance prüfen
version: 3
created: 2026-06-01
last_refined: 2026-07-10
use_when:
  - Vor Publish eines Blog-Artikels
  - Wenn Compliance-Status unklar
success_rate: 0.92
---

## Ablauf
1. Artikel-Text per MCP cms.get_draft laden
2. Guardrails-Check: pii_scan + brand_check
3. Bei Befund → human_review_request senden
4. Approval → cms.publish

## Bekannte Fallstricke
- PDFs aus E-Mail-Anhängen enthalten manchmal unstrukturierten PII → Schritt 2 doppelt laufen lassen
```

**Integration in AI-OS:**
- Skill-Store: `stack/data/skills/` (Markdown, versioniert im Git)
- Skill-Index: Qdrant-Collection `skills` + SQLite-FTS5
- Skill-Loader: Python-Modul `stack/scripts/tools/skill_loader.py`
- Trigger: am Ende jedes erfolgreichen Workflows (opt-in per Workflow-Definition)
- Kompatibilität: `agentskills.io`-Standard prüfen (AI-OS's Cursor-Skills schon kompatibel)

---

### K4 — Scheduler-Agent

**Der aktuell kritischste Blocker.**

**Was er können muss:**
- Cron-basierte Workflow-Ausführung (tägliches Briefing, wöchentliche Review, News-Aggregation)
- Natural-Language-Scheduling: `"jeden Morgen um 7 Uhr"` → Cron-Eintrag
- Delivery an beliebige MCP-Kanäle (Console, Mail, Messenger)
- Monitoring: `scheduler.status` → Console-Monitor-Route

**Optimal — Architektur:**

```
Scheduler-Agent (Python-Service)
  ├── Cron-Store: Postgres (schedule_jobs-Tabelle)
  ├── Job-Runner: ruft Workflow-Engine auf
  ├── Retry-Logik: LangGraph interrupt() bei Fehler
  ├── Delivery: MCP mail / mcp console / mcp slack
  └── API: GET /scheduler/jobs · POST /scheduler/jobs · DELETE /scheduler/jobs/{id}
```

**Beispiel-Jobs:**
```yaml
jobs:
  - id: daily-briefing
    cron: "0 7 * * *"
    workflow: daily-briefing
    delivery: [console, mail]
  - id: weekly-kg-review
    cron: "0 9 * * 1"
    workflow: kg-maintenance
    delivery: [console]
  - id: news-aggregation
    cron: "0 8,12,17 * * *"
    workflow: news-collect
    delivery: [console]
```

---

### K5 — Memory-System (3 Schichten vollständig)

**Aktuell:** L1 (Qdrant) produktiv, L2/L3 (Letta) teilweise.

**Optimal — vollständige 3-Schichten-Architektur:**

| Schicht | Speicher | Inhalt | Retention | Curator |
|---------|----------|--------|-----------|---------|
| **L1** | Qdrant | Chunks, Embeddings, Retrieval | 90 Tage rolling | `l1_curator.py` — dedupliziert, priorisiert |
| **L2** | Letta Postgres | Episodisches Gedächtnis, Agenten-Zustände, User-Modell | Dauerhaft | `l2_curator.py` — verdichtet L1-Episoden |
| **L3** | Neo4j / Postgres | Knowledge Graph — Entitäten, Beziehungen, Fakten | Dauerhaft, versioniert | `l3_curator.py` — extrahiert Fakten aus L2 |
| **Skills** | Markdown + Qdrant | Skill-Loop-Dokumente | Dauerhaft, versioniert | Skill-Loader (auto + manuell) |

**Memory-Flywheel:**
```
Aktion → L1 (Chunks) → L2 Curator (Episoden) → L3 Curator (Fakten/Graph)
                                                      ↓
                                              Skill-Destillation (bei Workflow-Ende)
                                                      ↓
                                              Context Bundle (beim nächsten Request)
```

---

### K6 — MCP-Gateway (M2/M3)

**Aktuell:** M1 produktiv (6 native Server).

**Optimal — M2/M3-Ausbau:**

| Phase | Server | Typ |
|-------|--------|-----|
| M1 ✅ | mail, cms, drive, web, kg, memory | Nativ (Python) |
| M2 | github, vercel, calendar | Extern (offizielle MCP-Server) |
| M3 | slack, notion, sap | Extern + Proxy |

**Architektur-Entscheidung M2/M3:**
- Externe MCP-Server werden **nicht direkt** vom Orchestrator angesprochen.
- Sie laufen als **Sidecar-Container** im Docker-Stack.
- MCP-Gateway bleibt der einzige Einstiegspunkt — Orchestrator spricht nur mit dem Gateway.

```
Orchestrator → MCP-Gateway → [native Server]
                           → [externe Sidecar: github-mcp, vercel-mcp, …]
```

---

### K7 — Knowledge Graph (vollständig)

**Aktuell:** Graph-Speicher vorhanden, UI und GraphRAG offen.

**Optimal:**

```
Entitäten:  Person, Firma, Projekt, Dokument, Serie, Skill, Workflow
Beziehungen: AUTHORED_BY, PART_OF, DEPENDS_ON, REFERENCES, PUBLISHED_TO
Spezial:    COMPLIANCE_CLEARED, REVIEWED_BY, SUPERSEDES (Skill-Versionen)
```

**GraphRAG-Modus:**
- Retrieval kombiniert Vektor-Suche (L1) + Graph-Traversal (L3)
- Kontext-Bundle erhält nicht nur Chunks, sondern auch Beziehungspfade
- Beispiel: `«Welche Artikel beziehen sich auf Kunde X und sind noch nicht Compliance-geprüft?»`

**Graph-UI in Console v2:**
- Interaktive Visualisierung (`/platform/kg`)
- Filter nach Entitäts-Typ, Zeitraum, Tenant
- Drill-down: Entität → alle verknüpften Dokumente/Workflows

---

## Tenant-Modell (Multi-Tenant-Erweiterung)

```
Tenant-Isolation:
  customers/{tenant}/
    ├── agents/           # Tenant-spezifische Agenten-Config
    ├── skills/           # Tenant-spezifische Skills (+ Platform-Skills erbend)
    ├── knowledge/        # Tenant-spezifische KG-Partition
    └── routing.md        # Tenant-Routing-Regeln

Pakete (SKUs):
  packages/
    ├── research-agent/   # AIOS-PACK-RESEARCH
    ├── blog-agent/       # AIOS-PACK-BLOG
    ├── email-agent/      # AIOS-PACK-EMAIL
    ├── time-agent/       # AIOS-PACK-TIME
    └── news-agent/       # AIOS-PACK-NEWS

Plattform-Garantien pro Tenant:
  - Isolierter Qdrant-Namespace
  - Isoliertes Letta-Projekt
  - Isolierte KG-Partition
  - Eigene Guardrails-Policy
  - Eigenes LiteLLM-Budget
```

---

## Ziel-Stack (Docker Compose)

```yaml
# Optimaler Ziel-Stack — Dienste und Rollen

services:

  # === Console ===
  console-web:       # Next.js :8092 — einzige UI, Legacy abgeschaltet
  console-api:       # FastAPI BFF :8093

  # === OS-Kernel ===
  orchestrator:      # :8091 — Intent-Router + Context-Builder + Audit
  workflow-engine:   # LangGraph-basiert — Checkpoint in Postgres
  skill-service:     # Skill-Loop + Skill-Store :8095
  scheduler-agent:   # Cron-Runner + Job-Store :8096

  # === MCP-Layer ===
  mcp-gateway:       # Zentraler MCP-Router :8097
  mcp-github:        # Sidecar: offiz. github-mcp
  mcp-vercel:        # Sidecar: offiz. vercel-mcp
  mcp-calendar:      # Sidecar: Google Calendar MCP

  # === Platform-Agenten ===
  pipeline-agent:    # RAG-Pipeline
  ingest-worker:     # Inbox-Polling → Qdrant
  memory-agent:      # L1/L2/L3-Curator
  guardrails-agent:  # L1/L2/L3-PII + Policies
  monitor-agent:     # Services + Workflow-Runs + FinOps

  # === Datenschicht ===
  qdrant:            # :6333 — L1 Vektor-Store
  letta:             # :8283 — L2/L3 Episodisch + User-Modell
  neo4j:             # :7474 — Knowledge Graph (ersetzt Postgres-KG)
  postgres-platform: # Pipeline-Log, Audit, Scheduler-Jobs, Workflow-Checkpoints
  postgres-letta:    # Letta intern
  postgres-litellm:  # LiteLLM intern

  # === LLM-Infrastruktur ===
  litellm:           # :4000 — Router, FinOps, Fallback-Logic
  searxng:           # :8888 — Privat-Suche

  # === Fach-Agenten (als Prozesse, nicht als Services) ===
  # research-agent, blog-agent, email-agent → laufen als Workflow-Steps
  # kein eigener Port — kommunizieren über Workflow-Engine + MCP
```

---

## Reifegradpfad

```
Heute (Juli 2026)                   Ziel-Architektur
──────────────────────────────────  ──────────────────────────────────
Console v2 produktiv           ✅   Console v2 vollständig (Blog in v2)
MCP Gateway M1                 ✅   MCP Gateway M2/M3 (GitHub, Vercel)
Workflow-Runner (eigen)        ✅   LangGraph-Engine darunter
Skill-Loader                   ⚠️   Skill-Loop vollständig (Hermes-Muster)
Scheduler-Agent                ⚠️   Scheduler-Agent produktiv
Memory L1 (Qdrant)             ✅   Memory L1/L2/L3 vollständig (Flywheel)
Memory L2/L3 (Letta)           ⚠️   Memory-Curator L2/L3 aktiv
Knowledge Graph (Speicher)     ✅   GraphRAG + Graph-UI in Console
Guardrails L1/L2               ✅   Guardrails L3 PII
Monitor (Services)             ✅   Monitor (Runs + FinOps + Alerts 24/7)
Legacy Console :8094           ⚠️   Abgeschaltet
A2A-Protokoll                  —    Inter-Agent-Standard
Neo4j (statt Postgres-KG)      —    Evaluieren vs. bestehender Ansatz
```

---

## Was diese Architektur kann (die anderen nicht)

| Fähigkeit | AI-OS optimal | Hermes | OpenClaw | LangGraph-Stack |
|-----------|--------------|--------|----------|-----------------|
| Multi-Tenant mit SKU-Paketen | ✅ | — | — | — |
| Deterministische Hülle + LLM-Facharbeit | ✅ | Partiell | — | ✅ |
| Skill-Loop mit Verfeinerung | ✅ (Ziel) | ✅ | ✅ | — |
| Knowledge Graph + GraphRAG | ✅ | — | — | Partiell |
| Deploybarer Stack mit UI | ✅ | — | Browser-UI | — |
| Guardrails / Compliance-Layer | ✅ | — | — | — |
| LLM-Router + FinOps | ✅ | — | — | — |
| Cron-Scheduler nativ | ✅ (Ziel) | ✅ | ✅ | Partiell |
| A2A Inter-Agent | ✅ (Ziel) | — | — | Partiell |

---

## Nächste konkrete Schritte (Priorisierung)

Abgeleitet aus dieser Architektur und der aktuellen ROADMAP:

| Prio | Task | Aufwand | Unblocks |
|------|------|---------|----------|
| P1 | Content Factory Blog-Pipeline → MCP-only (Console v2) | M | Legacy-Abschaltung |
| P1 | Skill-Loader nach Hermes-Muster implementieren | M | Team-Parität, Lernfähigkeit |
| P1 | Guardrails L3 PII abschließen | S | Enterprise-Readiness |
| P2 | Scheduler-Agent bauen | M | Briefing-Cron, News, Time-Agent |
| P2 | Memory-Curator L2/L3 fertigstellen | M | Memory-Flywheel |
| P2 | LangGraph als Workflow-Runner-Engine evaluieren | S | Scalability, Observability |
| P3 | GraphRAG + Graph-UI in Console | L | Knowledge-Discovery |
| P3 | MCP-Gateway M2 (GitHub, Vercel, Calendar) | M | External integrations |
| P4 | Neo4j vs. Postgres-KG evaluieren | S | Graph-Performance |
| P4 | Monitor 24/7 (Alerts, FinOps-Dashboard) | M | Produktions-Betrieb |

*Aufwand: S = < 1 Tag · M = 2–5 Tage · L = 1–2 Wochen*

---

## Zusammenfassung

AI-OS optimal ist kein Neustart — es ist der heutige Stack mit fünf gezielten Ergänzungen:

1. **Skill-Loop** (nach Hermes-Muster) — Agenten werden mit jeder Aufgabe klüger.
2. **LangGraph-Engine** unter dem Workflow-Runner — Production-grade Orchestrierung ohne eigenen Bau.
3. **Scheduler-Agent** — Autonomes Ausführen von Workflows nach Plan.
4. **GraphRAG + Graph-UI** — Knowledge Graph wird suchbar und nutzbar.
5. **Memory-Flywheel vollständig** — L1 → L2 → L3 → Skill ist geschlossen.

Das Ergebnis ist eine Plattform, die **mit jeder Nutzung klüger wird**, **souverän bleibt**, **mehrere Kunden** bedienen kann und **keine Cloud-Abhängigkeit** hat.
