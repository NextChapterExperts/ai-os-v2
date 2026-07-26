# AI-OS v2 — Detaillierte Bauanleitung

**Für:** LLMs, Entwickler, die das System von Grund auf bauen  
**Zweck:** Vollständige technische Spezifikation — ausreichend detailliert um ohne zusätzlichen Kontext zu starten  
**Basis:** AI-OS v1 (../1000-AI-OS) — eingefroren Juli 2026  
**Stand:** Juli 2026 (aktualisiert 2026-07-26 — Context-Bundle Optimierung (6 Slices <50ms) in `context_resolution.py` [P1/P13] & LangGraph Checkpointing & Resume in `workflow_engine/` [P7/P15] abgeschlossen; 63 Pytest-Tests grün)  
**Modus:** **Eine Implementierung** — keine Alternativen in dieser Roadmap. Jede Entscheidung ist final.  
**Detail-Spec Company Brain:** [docs/09-COMPANY-BRAIN.md](docs/09-COMPANY-BRAIN.md) · **Memory einfach:** [docs/10-MEMORY-EINFACH.md](docs/10-MEMORY-EINFACH.md) · **Kontext Lagebild→LLM:** [docs/14-KONTEXT.md](docs/14-KONTEXT.md)  
**Erstes Lizenzprodukt (VM):** [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md)  
**Leitprinzipien detailliert:** [docs/12-LEITPRINZIPIEN.md](docs/12-LEITPRINZIPIEN.md)  
**Agenten-Workflow (Verbindlich):** [AGENTS.md](AGENTS.md) (Der 6-Schritte-Ablauf vor & nach Änderungen)

---

## Design-Manifest

AI-OS v2 ist ein **state-of-the-art, souveränes KI-Betriebssystem** mit genau einem technischen Pfad:

| Ziel | Wie v2 es erreicht |
|------|-------------------|
| **Kosten sparen** | Default-Inference über Ollama (€0/Token). Cloud bewusst via OpenRouter (`:free` auf DEV, `:floor` in PROD). Skill-Loop reduziert wiederholte LLM-Calls. FinOps in LangFuse pro Tenant/Modell. |
| **Qualität erhöhen** | Context Bundle (6 Slices) + GraphRAG + Unified Search vor jedem LLM-Call. Guardrails + Human-in-the-Loop. Capability-Tests gegen lokales Modell. |
| **Skalierbar** | Layered Deployment (Infra → Core → Platform → Fach). Tenant-Runtime-Isolation. Postgres-Checkpoints. Horizontale Skalierung über Compose-Profile. |
| **Erweiterbar** | MCP-Gateway + SDK-Contract. Fach-Agenten als SKU-Pakete. Skills versioniert. Neue Agenten = neues Compose-File + Contract-Tests. |

**Produkt-Start (verbindlich):** Auslieferung als **Platform-VM-Appliance** — erstes Lizenzprodukt = VM + `AIOS-CORE`.  
Leitgedanke: *Eine VM · eine Tür (Memory Gateway) · ein Gedächtnis **pro VM** (inkl. Capture).*  

**Isolationsmodell (verbindlich):** Eine Welt = eine VM = ein Company Brain.  
- **NCE DEV-VM** = First-Party: Peter/NCE nutzen Company Brain selbst (Cursor/Antigravity → dieses Brain).  
- **Kunden-PROD-VM** = eigenes Brain, eigene Volumes/DB — kein Auto-Sync von NCE.  
Spec: [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md) § Isolationsmodell.

### Der festgelegte Stack (keine Abweichung)

```
Ubuntu 26.04 LTS · Docker Compose · KVM-VM
Postgres+pgvector · Qdrant · Letta · LiteLLM
Ollama (Default) · OpenRouter (Cloud) · LangFuse · SearXNG
LangGraph · MCP-Gateway · Unified Search · Memory Gateway
Next.js 15 Console · Python 3.12 FastAPI · Pydantic v2 SDK
Caddy · ntfy · Docling · Playwright-MCP
```

---

## Inhaltsverzeichnis

1. [Kontext & Prinzipien](#1-kontext--prinzipien)
2. [Repository-Struktur](#2-repository-struktur)
3. [Technologie-Stack](#3-technologie-stack)
4. [Schichtenmodell & Datenfluss](#4-schichtenmodell--datenfluss)
5. [Phase 0 — Platform-VM Fundament & Tooling](#5-phase-0--platform-vm-fundament--tooling)
6. [Phase 1 — Core OS + Memory Gateway](#6-phase-1--core-os--memory-gateway)
6b. [Phase 1b — Chat Capture](#6b-phase-1b--chat-capture--externe-chats-ins-gedächtnis)
7. [Phase 2 — Platform-Agenten](#7-phase-2--platform-agenten)
8. [Phase 3 — Agent-SDK & Contract](#8-phase-3--agent-sdk--contract)
9. [Phase 4 — Fach-Agenten](#9-phase-4--fach-agenten) *(erst nach Platform-Gate)*
10. [Phase 5 — Console vollständig](#10-phase-5--console-vollständig)
11. [Phase 6 — Multi-Tenant & GraphRAG](#11-phase-6--multi-tenant--graphrag)
12. [Datenschicht im Detail](#12-datenschicht-im-detail) *(inkl. [§12.4 Company Brain](#124-company-brain--wissensmanagement))*
13. [MCP-Gateway im Detail](#13-mcp-gateway-im-detail)
14. [Skill-Loop im Detail](#14-skill-loop-im-detail)
15. [Tenant-Modell im Detail](#15-tenant-modell-im-detail)
16. [Test-Strategie](#16-test-strategie)
17. [Was aus v1 übernommen wird](#17-was-aus-v1-übernommen-wird)
18. [Bekannte Fallstricke aus v1](#18-bekannte-fallstricke-aus-v1)
19. [Deployment & Skalierung](#19-deployment--skalierung) *(inkl. Isolationsmodell NCE≠Kunde)*
20. [Monitoring: LangFuse](#20-monitoring-langfuse)
21. [Produktions-Stack](#21-produktions-stack)
22. [Festgelegter Technologie-Stack](#22-festgelegter-technologie-stack)
23. [Inference: Ollama + OpenRouter](#23-inference-ollama--openrouter)

---

## 1. Kontext & Prinzipien

### Was AI-OS ist

AI-OS ist ein **souveränes, self-hosted KI-Betriebssystem** für Einzelpersonen und kleine Teams. Es ist kein Chatbot, kein Copilot, keine SaaS-Plattform. Es ist eine deploybare Infrastruktur, die:

- Wissen **speichert, verknüpft und schützt** (L0–L3 + Knowledge Graph)
- Agenten **orchestriert** mit deterministischen Hüllen (kein LLM-Dispatch)
- Externe Konnektivität **ausschließlich über MCP** erlaubt
- Mehrere **Tenants mit isolierten Paketen** (SKUs) bedient
- Mit jeder Nutzung **klüger wird** (Skill-Loop + Memory-Flywheel)

### Unveränderliche Leitprinzipien (P1–P19)

**Vollständige Spec** (Intent · Regeln · Verboten · Wo · Abnahme):  
→ **[docs/12-LEITPRINZIPIEN.md](docs/12-LEITPRINZIPIEN.md)**

Kurzform (Detail immer in docs/12):

| | Prinzip | Muss / Kernregel |
|--|---------|------------------|
| P1 | Kontextsystem vor Agenten | Jeder Dispatch = Context Bundle (7 Slices); Agent baut kein eigenes RAG |
| P2 | Nicht alles speichern | Schichtregeln; LLM setzt nie `storage_target`; L1 nur published |
| P3 | Graph vor reinem RAG | Beziehungen in G; Search mit Graph/Fusion, nicht nur Vektor |
| P4 | Determinismus in der Hülle | Dispatch, Guardrails, Audit, FinOps, License = Code; LLM = Facharbeit |
| P5 | MCP einzige Konnektivität | Nur `self.mcp`; Allowlist + Caps + Audit; kein Direkt-HTTP im Agent |
| P6 | Skill-Loop | Erfolg → versionierter Skill → SkillSlice bei Wiederholung |
| P7 | State-Machine | LangGraph + Postgres-Checkpoints; resumierbar |
| P8 | Agent-Contract | SDK Pflicht; In/Out = DataProduct; Tenant explizit |
| P9 | Alles in die DB | Run-Ende: A Pflicht + DP/G/… laut Schema; kein „nur RAM“ |
| P10 | Platform vor Fach | Platform-Gate grün vor jedem `deploy/agents/*` |
| P11 | Search + Memory Gateway | Eine Suche; eine Inference-Tür mit Persist-Hook |
| P12 | FinOps | Default `sovereign`; ≥80 % lokal; Cloud in LangFuse + Audit |
| P13 | Qualität durch Kontext | Erst Bundle/Retrieval/Skill, dann Premium |
| P14 | Ein Stack | Dev→Enterprise = gleiche Compose-Architektur |
| P15 | PGE-Trinity | Planner(LLM) → Gatekeeper(Code) → Executor |
| P16 | Observer | Lokaler Qualitätscheck; fails open; Audit bei Verstoß |
| P17 | Hash-Audit | `prev_hash`/`entry_hash` + signierte Run-Receipts |
| P18 | Company Brain | SSOT = K+G+L1; Letta ≠ Wahrheit; DP-Commit only — [09](docs/09-COMPANY-BRAIN.md) |
| P19 | Platform-VM first | VM+Core = Produkt; **1 VM = 1 Brain**; NCE First-Party auf DEV — [11](docs/11-PLATFORM-VM.md) |

Verletzung eines Ps = Architekturfehler. Änderungen nur per ADR + Update von docs/12.

### Was v2 von v1 unterscheidet

v1 hat alle Konzepte, aber:
- Der Agent-Contract ist optional → Agenten umgehen ihn
- Multi-Tenant ist Ordnerstruktur, keine Laufzeit-Isolation
- Workflow-Engine ist eigener Code → LangGraph wäre besser
- Skill-Loop ist P1-Baustelle
- Scheduler ist P2-Blocker
- UI zeigt zu viel auf falscher Ebene
- Monitoring (LangFuse) war optional → in v2 **ab Tag 1 Pflicht**
- Daten landeten teils nur in Dateien/Logs → v2 **P9: alles in DB**
- Suche und Modellwahl waren verstreut → v2 **zentrale Platform-Services**
- Guardrails waren nachgelagert → v2 **PGE-Gatekeeper vor jedem Tool-Call (P15)**
- Keine Antwort-Qualitätsprüfung → v2 **Observer Audit Layer (P16)**
- Audit war einfaches Log → v2 **hash-chained + signierte Belege (P17)**

v2 löst das durch: **Platform zuerst vollständig, dann Fach-Agenten als SKU-Pakete.**

### Markt-validierte Muster (aus Wettbewerbsanalyse, siehe docs/08-MARKTVERGLEICH.md)

Übernommen aus reifen Projekten (Cognithor, Synesis, Olla Nest, ArcaQ, Verisa), eingepasst in den festen Stack:

| Muster | Prinzip/Phase | Ziel |
|--------|---------------|------|
| PGE-Trinity (Planner→Gatekeeper→Executor) | P15 · Phase 1+2 | Qualität, Sicherheit |
| Observer Audit Layer | P16 · Phase 2 | Qualität (kostenlos, lokal) |
| Hash-chained Audit + Run-Receipts | P17 · Phase 0+2 | Compliance, FinOps |
| Redaction-Gateway vor Cloud | Phase 2 (Guardrails) | Kosten, DSGVO |
| Auto-Router mit Modell-Scoring | Phase 1 (Model Gateway) | Kosten, Qualität |
| CAG (KV-Cache-Reuse) | Phase 1 (Model Gateway) | Kosten |
| Planner→Retrieval→Writer→Critic | Phase 4 (Fach-Workflows) | Qualität |
| Score-Fusion in Unified Search | Phase 1 (Search) | Qualität |
| Working- + Tactical-Memory | Phase 2 (Memory) | Qualität |
| `_safe_call()`-Konvention | Phase 3 (SDK) | Robustheit |
| Deterministic Replay | Phase 1 (Workflow) | Debugging |
| Coverage-Gate + Hypothesis-Tests | Phase 0 (Tooling) | Reife |
| ADRs für finale Entscheidungen | durchgängig | Klarheit |
| One-Command-Demo-Modus | Phase 5 (Console) | Time-to-Value |
| Company Brain (org:* SSOT, nicht Second Brain) | P18 · Phase 2+ · §12.4 | Wissensqualität |
| Platform-VM + Memory Gateway + Chat Capture | P19 · Phase 0–1b · docs/11 | Erstes Lizenzprodukt |
| VM-Isolation (NCE-Brain ≠ Kunden-Brain) | P19 · Phase 0+ · docs/11 | Datenschutz, First-Party |

### Build-Reihenfolge (verbindlich)

```
Phase 0   Platform-VM Scaffold + Infra + LangFuse + DB-Schema
          + DEV-VM-Bootstrap (NCE First-Party Company Brain auf dieser VM)
Phase 1   Core OS + Unified Search + Memory Gateway + LangFuse-Tracing
Phase 1b  Chat Capture → Speicher DIESER VM (NCE-Brain auf DEV)
Phase 2   Platform-Agenten vollständig → PLATFORM-GATE
Phase 3   Agent-SDK (Platform-Agenten migrieren)
───────   ⛔ Kein Fach-Agent vor bestandenem Platform-Gate
Phase 4   Fach-Agenten (Research, Blog, Email, Kommunikationsmanager, time-agent …)
Phase 5   Console vollständig
Phase 6   Multi-Tenant (innerhalb einer VM) + GraphRAG
          ⚠ ersetzt NICHT die physische VM-Grenze zu Kunden
```

Produkt-Sicht + Isolationsmodell: [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md).

---

## 2. Repository-Struktur

```
ai-os-v2/
│
├── README.md
├── ROADMAP.md                          # Dieses Dokument
├── .env.example                        # Alle benötigten Variablen
├── .gitignore
│
├── appliance/                          # P19 — VM-Build (cloud-init, image-build, defaults)
│   ├── image-build.sh
│   ├── cloud-init/
│   └── config/defaults/
│
├── deploy/                             # Docker Compose — 3 Modi (in der VM)
│   ├── infra.yml                       # Qdrant, Letta, Postgres, LiteLLM, SearXNG
│   ├── monitoring.yml                  # LangFuse + postgres-langfuse (ab Tag 1, nicht optional)
│   ├── core.yml                        # Modus 1: OS + Memory Gateway
│   ├── platform-agents.yml             # Modus 2: + Platform-Agenten
│   ├── chat-capture.yml                # Phase 1b: Gemini/Antigravity Capture
│   ├── agents/                         # Modus 3: Fach-Agenten (erst nach Platform-Gate)
│   │   ├── research.yml
│   │   ├── blog.yml
│   │   ├── email.yml
│   │   ├── time.yml
│   │   └── news.yml
│   └── profiles/                       # dev-vm.yml (Cursor-Hinweise) · prod-vm.yml
│
├── core/                               # Das OS — läuft ohne Agenten
│   ├── orchestrator/                   # Intent-Router, Context-Builder, Audit
│   │   ├── server.py                   # FastAPI :8091
│   │   ├── intent_router.py            # Intent → Delegate
│   │   ├── context_resolution.py       # Context Bundle (6 Slices) ← v1 portiert
│   │   ├── dispatch.py                 # Generischer Delegate
│   │   └── audit.py                   # AgentRun + Log
│   │
│   ├── search-service/                 # NEU v2 — Unified Search (Platform-Kern)
│   │   ├── server.py                   # FastAPI :8094
│   │   ├── unified_search.py           # L1 + G + SK + A — ein Endpoint
│   │   └── index_hooks.py              # Auto-Index nach jedem DP-Commit
│   │
│   ├── model-gateway/                  # NEU v2 — LLM-Modellauswahl (Platform-Kern)
│   │   ├── registry.py                 # Verfügbare Modelle (Ollama, OpenRouter, …)
│   │   ├── compute_modes.py            # sovereign | balanced | premium | coding
│   │   └── finops.py                   # Kosten-Tracking → LangFuse + ai_os_log
│   │
│   ├── workflow-engine/                # LangGraph-basierte Workflow-Engine
│   │   ├── engine.py                   # LangGraph StateGraph Wrapper
│   │   ├── checkpoint_store.py         # Postgres-backed Checkpointing
│   │   ├── workflows/                  # Workflow-Definitionen
│   │   │   ├── daily_briefing.py
│   │   │   ├── research_workflow.py
│   │   │   └── blog_workflow.py
│   │   └── human_in_loop.py           # interrupt() Primitive
│   │
│   ├── skill-service/                  # Skill-Loop
│   │   ├── skill_store.py              # Markdown + Qdrant + SQLite-FTS5
│   │   ├── skill_distiller.py          # Task → Skill-Dokument (LLM-gesteuert)
│   │   ├── skill_loader.py             # Context-Bundle Integration
│   │   └── skill_refiner.py           # Skill verbessern bei Wiederholung
│   │
│   ├── scheduler/                      # Cron-Runner
│   │   ├── scheduler_service.py        # Cron-Store + Job-Runner
│   │   ├── job_store.py                # Postgres: schedule_jobs
│   │   ├── natural_language_parser.py  # «jeden Morgen um 7 Uhr» → Cron
│   │   └── delivery.py                # MCP-Delivery an Kanäle
│   │
│   ├── mcp-gateway/                    # Einziger Konnektivitäts-Layer
│   │   ├── gateway.py                  # FastAPI :8097
│   │   ├── registry.py                 # Server-Allowlist + Caps
│   │   ├── audit.py                   # Pro-Call-Audit
│   │   └── adapters/                  # Native MCP-Adapter
│   │       ├── web_search.py           # ← v1 portiert
│   │       ├── mail.py                 # ← v1 portiert
│   │       ├── cms_git.py              # ← v1 portiert
│   │       ├── calendar.py             # ← v1 portiert
│   │       ├── qdrant_search.py        # ← v1 portiert
│   │       └── memory.py              # ← v1 portiert
│   │
│   ├── memory/                         # L1/L2/L3 Curators
│   │   ├── l1_curator.py               # ← v1 portiert
│   │   ├── l2_curator.py               # Episoden aus L1 verdichten
│   │   └── l3_curator.py              # Fakten aus L2 → KG
│   │
│   └── console/                        # Next.js 15 — 3-Ebenen-IA
│       ├── package.json
│       ├── src/app/
│       │   ├── page.tsx                # Ebene 1: Lagebild
│       │   ├── workflows/              # Ebene 2: Workflows + Scheduler
│       │   │   ├── page.tsx
│       │   │   ├── [id]/page.tsx
│       │   │   └── briefing/page.tsx
│       │   ├── platform/               # Ebene 3: Plattform-Details
│       │   │   ├── page.tsx
│       │   │   ├── mcp/page.tsx
│       │   │   ├── kg/page.tsx          # Knowledge Graph UI
│       │   │   ├── skills/page.tsx
│       │   │   ├── monitor/page.tsx
│       │   │   └── agents/page.tsx
│       │   └── api/                    # API-Routen (BFF)
│       └── src/lib/
│
├── sdk/                                # Agent-SDK — Contract für jeden Agenten
│   ├── agent_base.py                   # Basisklasse: Input-DP, Output-DP, MCP
│   ├── dataproduct.py                  # DP-Schema + Validator ← v1 portiert
│   ├── schema_registry.py              # L0-Schemas ← v1 portiert
│   ├── mcp_adapter.py                  # MCP-Wrapper
│   ├── skill_hook.py                   # Post-Task Skill-Destillation
│   ├── tenant_context.py               # Tenant-Kontext-Träger
│   ├── contract_validator.py           # Prüft Agent-Contract zur Laufzeit
│   ├── agent_template/                 # Scaffolding: `aios new-agent <name>`
│   │   ├── agent.py.template
│   │   ├── schema.yaml.template
│   │   └── README.md.template
│   └── tests/                          # Contract-Tests — alle Agenten müssen bestehen
│       ├── test_contract.py
│       ├── test_dataproduct.py         # ← v1 portiert + erweitert
│       └── test_mcp_adapter.py
│
├── platform-agents/                    # OS-Schicht — separat deploybar
│   ├── pipeline-agent/                 # RAG-Pipeline ← v1 portiert
│   ├── ingest-agent/                   # Inbox-Polling ← v1 portiert
│   ├── memory-agent/                   # L1/L2/L3 Curators
│   ├── guardrails-agent/               # Policy-Enforcement ← v1 portiert + L3
│   ├── monitor-agent/                  # Observability ← v1 portiert
│   └── scheduler-agent/               # Cron-Runner (NEU)
│
├── agents/                             # Fach-Agenten — als SKU-Pakete
│   ├── research/                       # AIOS-PACK-RESEARCH ← v1 portiert
│   ├── blog/                           # AIOS-PACK-BLOG ← v1 portiert
│   ├── email/                          # AIOS-PACK-EMAIL ← v1 portiert
│   ├── time/                           # AIOS-PACK-TIME
│   └── news/                           # AIOS-PACK-NEWS
│
├── packages/                           # Schema-/Seed-SKUs (nicht immer eigener Agent-Prozess)
│   └── org-brain/                      # P18 Company Brain — L0 entities/edges + Seed-Hints
│       ├── schema/entities.yaml
│       ├── schema/edges.yaml
│       └── README.md
│
├── customers/                          # Tenant-Profile ← v1 portiert
│   ├── _template/
│   ├── nextchapter/                    # NCE First-Party Tenant (DEV-VM Company Brain, P18/P19)
│   └── platform-test/
│
├── config/                             # Zentrale YAML-Konfigurationen
│   ├── agents-registry.yaml            # ← v1 portiert
│   ├── assistants-registry.yaml        # ← v1 portiert
│   ├── packages.yaml                   # SKU-Definitionen (inkl. org-brain)
│   ├── kg-platform-schema.yaml         # Platform-KG-Kern (+ Verweis org-brain)
│   ├── platform-storage-rules.yaml     # ← v1 portiert
│   ├── kg-platform-schema.yaml         # ← v1 portiert
│   ├── litellm-config.yaml             # ← v1 portiert
│   └── compute.yaml                    # ← v1 portiert
│
├── tests/                              # Integrations + Golden Tests
│   ├── test_contract.py                # Agent-Contract-Tests
│   ├── test_dataproduct.py
│   ├── test_workflow.py
│   ├── test_mcp.py
│   ├── test_context.py
│   ├── test_skill_loop.py
│   └── golden/                         # Golden-Query-Tests ← v1 portiert
│
└── docs/                               # Dokumentation
    ├── 00-VISION.md
    ├── 01-ARCHITEKTUR.md
    ├── 02-AGENT-SDK.md
    ├── 03-DATENPRODUKTE.md
    ├── 04-DEPLOYMENT.md
    ├── 05-CONSOLE-IA.md
    └── ref/                            # Referenz-Dokumente aus v1
```

---

## 3. Technologie-Stack

### Infrastruktur

| Komponente | Technologie | Port | Zweck |
|-----------|-------------|------|-------|
| Container | Incus/LXC (Ubuntu 26.04) | — | Isolation vom Host |
| Orchestrierung | Docker Compose | — | Service-Management |
| Vektordatenbank | Qdrant 1.x | 6333 | L1 Semantic Search |
| Agenten-Memory | Letta | 8283 | L2/L3 Episodisches Gedächtnis |
| Knowledge Graph | Postgres + pgvector | 5432 | G — Entities + Edges |
| LLM-Router | LiteLLM | 4000 | Modell-agnostisch, FinOps |
| Observability | LangFuse (self-hosted) | 3000 | Traces, FinOps, Evals — **ab Tag 1** |
| Unified Search | search-service | 8094 | Suche über L1 + G + SK + A |
| Model Gateway | model-gateway (in Core) | intern | Modellauswahl, Default: Ollama lokal |
| Websuche | SearXNG | 8888 | Private Web-Suche |
| Inference lokal | Ollama (LAN) | 11434 | **Default** — sovereign, €0/Token |
| Inference Cloud | OpenRouter via LiteLLM | extern | balanced/premium — ein Cloud-Gateway |

### Applikations-Stack

| Komponente | Technologie | Warum |
|-----------|-------------|-------|
| Orchestrator | Python 3.12 + FastAPI | Determinismus, bestehende v1-Codebase |
| Workflow-Engine | Python + LangGraph | Battle-tested Orchestrierung, Checkpointing |
| MCP-Gateway | Python + FastAPI | Bestehende v1-Adapter |
| Skill-Service | Python | Markdown + Qdrant + SQLite-FTS5 |
| Scheduler | Python + APScheduler | Cron + Natural-Language |
| Console | Next.js 15 + TypeScript | Bestehende v1-Codebase |
| Agent-SDK | Python 3.12 | Pydantic für DP-Validation |

### Neue Dependencies (v2 gegenüber v1)

```
langgraph>=0.4          # Workflow-Engine
langchain-core>=0.3     # LangGraph Dependency
langfuse>=2.0           # Tracing ab Tag 1 (self-hosted)
apscheduler>=3.10       # Scheduler
sqlite-utils>=3.35      # FTS5 Skill-Index
pydantic>=2.7           # SDK Contract-Validation (v1 hatte 1.x)
```

---

## 4. Schichtenmodell & Datenfluss

```
┌─────────────────────────────────────────────────────────────────────┐
│ SCHICHT 0 — HOST                                                     │
│ Cursor IDE · Browser · ~/ai-os.sh · Werkstatt-Queue                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ Incus-Proxy
┌────────────────────────────────▼────────────────────────────────────┐
│ SCHICHT 1 — CONSOLE (Mensch-Maschine-Grenze)                        │
│                                                                      │
│  Next.js :8092                    console-api BFF :8093              │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────────────┐  │
│  │ Lagebild    │ │ Workflows   │ │ Plattform (selten)            │  │
│  │ (täglich)  │ │ (wöchentl.) │ │ MCP · KG · Skills · Monitor  │  │
│  └─────────────┘ └─────────────┘ └──────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ JSON / REST
┌────────────────────────────────▼────────────────────────────────────┐
│ SCHICHT 2 — ORCHESTRATOR (OS-Kernel :8091)                          │
│                                                                      │
│  Intent-Router → Context-Builder (6 Slices) → Dispatch → Audit     │
│  [Deterministisch — kein LLM-Dispatch]                              │
│                                                                      │
│  Workflow-Engine (LangGraph :intern)                                 │
│  Skill-Service (:8095)                                               │
│  Scheduler (:8096)                                                   │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
  ┌─────────┐ ┌────────┐ ┌───────┐ ┌────────┐ ┌──────────────────┐
  │ MCP-    │ │Pipeline│ │Ingest │ │Memory  │ │ Guardrails       │
  │ Gateway │ │ Agent  │ │ Agent │ │ Agent  │ │ Agent            │
  │ :8097   │ │        │ │       │ │        │ │                  │
  └─────┬───┘ └────────┘ └───────┘ └────────┘ └──────────────────┘
        │
   ┌────▼──────────────────────────────────────────────────────┐
   │ SCHICHT 3 — MCP-SERVER                                    │
   │ mail · cms · drive · web · kg · memory (nativ)            │
   │ github · vercel · calendar (extern, Sidecar)              │
   └────┬──────────────────────────────────────────────────────┘
        │
   ┌────▼──────────────────────────────────────────────────────┐
   │ SCHICHT 4 — DATENSCHICHT                                  │
   │                                                            │
   │  L0  schema_registry (YAML)                               │
   │  K   Dateisystem content/ + knowledge/                    │
   │  G   Postgres knowledge_graph (kg_nodes, kg_edges)        │
   │  L1  Qdrant (kuratiert, 90-Tage-Rolling)                  │
   │  L2  Letta Postgres (episodisch, dauerhaft)               │
   │  L3  Letta Core (User-Modell, Fakten)                     │
   │  SK  SQLite + Qdrant (Skills, dauerhaft)                  │
   │  A   Postgres ai_os_log (Audit, unveränderlich)           │
   └────┬──────────────────────────────────────────────────────┘
        │
   ┌────▼──────────────────────────────────────────────────────┐
   │ SCHICHT 5 — INFERENCE                                     │
   │ LiteLLM :4000 → Ollama LAN · OpenRouter · Anthropic       │
   └───────────────────────────────────────────────────────────┘
```

### Datenflusskarte (normaler Request)

```
1. Nutzer tippt Intent in Console
2. Console → POST /v1/dispatch {intent, tenant_id, params}
3. Orchestrator: intent_router → Workflow-Name bestimmen
4. Orchestrator: context_resolution → Context Bundle (6 Slices)
5. Orchestrator: skill_loader → passende Skills aus Skill-Store laden
6. Orchestrator: guardrails_check → Policies + PII-Scan
7. Workflow-Engine: LangGraph-Graph starten mit State{context_bundle, tenant, ...}
8. Workflow-Nodes: Agenten laufen, rufen MCP-Gateway auf, produzieren DPs
9. DP-Commit: jedes DP → schema validate → G (KG) + K (files) + ggf. L1
10. Workflow-Ende: Skill-Hook → Skill-Dokument destillieren (wenn komplex)
11. AgentRun-Record in Audit-Log
12. Response → Console: Output-DP-Ref + Status
```

---

## 5. Phase 0 — Platform-VM Fundament & Tooling

**Dauer:** 2–4 Tage (Repo + Appliance-Scaffold + Infra)  
**Ziel:** Repo mit Konventionen, **`appliance/`-Scaffold**, laufender Infra **inkl. LangFuse**, CI-Grundstruktur, DB-Schema, dokumentierter **DEV-VM-Bootstrap**  
**Produkt-Kontext:** Phase 0 ist der Boden der **Platform-VM** (P19) — nicht „nur Docker auf dem Laptop“. Spec: [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md).  
**Akzeptanzkriterium:**
- `docker compose -f deploy/infra.yml -f deploy/monitoring.yml up -d` → alle Services healthy
- `appliance/` vorhanden (Build-Skript-Stub + Defaults)
- DEV-VM-Bootstrap (Ubuntu Desktop + Docker + Cursor/Antigravity-Hinweise) in Docs lauffähig beschrieben

### 5.1 Repository anlegen

```bash
# Neues Repo, kein Fork von v1 — Ziel-Laufzeitort: Platform-VM
git init ai-os-v2
cd ai-os-v2
mkdir -p appliance/cloud-init appliance/config/defaults deploy/profiles
git commit --allow-empty -m "chore: initial commit"
```

### 5.2 .env.example

```env
# LLM — Default: lokal (Ollama LAN)
LITELLM_PORT=4000
OLLAMA_HOST=192.168.178.64
OLLAMA_PORT=11434
OLLAMA_DEFAULT_MODEL=qwen3.6-64k:latest
DEFAULT_COMPUTE_MODE=sovereign          # sovereign | balanced | premium | coding

# Cloud — OpenRouter (balanced/premium/coding); Key leer = nur sovereign
OPENROUTER_API_KEY=

# LangFuse (Pflicht ab Tag 1)
LANGFUSE_HOST=http://langfuse:3000
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_PG_PW=

# Datenbank
POSTGRES_HOST=postgres-platform
POSTGRES_DB=aios
POSTGRES_USER=aios
POSTGRES_PASSWORD=

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_CONTENT=content
QDRANT_COLLECTION_SKILLS=skills

# Letta
LETTA_HOST=letta
LETTA_PORT=8283
LETTA_API_KEY=

# Services
ORCHESTRATOR_PORT=8091
CONSOLE_PORT=8092
CONSOLE_API_PORT=8093
MCP_GATEWAY_PORT=8097
SKILL_SERVICE_PORT=8095
SCHEDULER_PORT=8096

# Tenant
DEFAULT_TENANT=nextchapter

# Compute-Modus: sovereign | balanced | premium | coding
DEFAULT_COMPUTE_MODE=sovereign
AIOS_COMPUTE_MODE_PATH=/opt/ai-os/memory/state/compute-mode.json
```

### 5.3 Python-Konventionen

```
- Python 3.12
- Pydantic v2 für alle Datenmodelle
- FastAPI für alle HTTP-Services
- Pytest für alle Tests + Hypothesis (property-based) für Kernlogik
- Coverage-Gate: 85 % — CI bricht bei Unterschreitung (Vorbild Cognithor)
- Ruff für Linting, mypy --strict für sdk/ und core/
- Keine globalen Singletons — alles dependency-injected
- Kein LLM-Import außerhalb von sdk/mcp_adapter.py und workflow-nodes
- Fehlerbehandlung: einheitliches _safe_call()-Muster statt stillem except:pass
  → Failure-Registry pro Funktion + Circuit-Breaker (Vorbild Cognithor)
- Jede finale Architektur-Entscheidung als ADR in docs/adr/
```

### 5.4 Docker Compose — Infra-Baseline + LangFuse

```yaml
# deploy/infra.yml — wird von allen Modi included
version: "3.9"
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333", "6335:6335"]
    volumes: ["qdrant_data:/qdrant/storage"]

  letta:
    image: lettaai/letta:latest
    ports: ["8283:8283", "8083:8083"]
    environment:
      LETTA_PG_URI: postgresql://letta:letta@postgres-letta:5432/letta

  postgres-platform:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: aios
      POSTGRES_USER: aios
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes: ["postgres_platform_data:/var/lib/postgresql/data"]

  postgres-letta:
    image: postgres:16
    environment:
      POSTGRES_DB: letta
      POSTGRES_USER: letta
      POSTGRES_PASSWORD: letta

  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    ports: ["4000:4000"]
    volumes: ["./config/litellm-config.yaml:/app/config.yaml"]

  searxng:
    image: searxng/searxng:latest
    ports: ["8888:8888"]

volumes:
  qdrant_data:
  postgres_platform_data:
  postgres_letta_data:
```

```yaml
# deploy/monitoring.yml — ab Tag 1 mitstarten (nicht optional)
services:
  langfuse:
    image: langfuse/langfuse:latest
    ports: ["3000:3000"]
    environment:
      DATABASE_URL: postgresql://langfuse:${LANGFUSE_PG_PW}@postgres-langfuse/langfuse
      NEXTAUTH_SECRET: ${LANGFUSE_SECRET}
      SALT: ${LANGFUSE_SALT}
    depends_on: [postgres-langfuse]

  postgres-langfuse:
    image: postgres:16
    environment:
      POSTGRES_DB: langfuse
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: ${LANGFUSE_PG_PW}
```

**Start-Befehl Phase 0:**
```bash
docker compose -f deploy/infra.yml -f deploy/monitoring.yml up -d
curl http://localhost:3000/api/public/health   # LangFuse
```

### 5.4b Appliance-Scaffold + DEV-VM (P19)

```text
appliance/
├── image-build.sh          # Stub → später qcow2 / cloud-init Image
├── cloud-init/             # user-data: Docker, user aios, ssh
└── config/defaults/        # .env.template, license.yaml.example
deploy/profiles/
├── dev-vm.yml              # Hinweise/Overrides DEV (Ports, Volumes für Cursor-Inbox)
└── prod-vm.yml             # headless, kein Dev-Tooling
```

**DEV-VM (NCE-Werkstatt):** Ubuntu 26.04 Desktop in KVM — Cursor, Antigravity, Git, Docker, AI-OS-Compose.  
→ **Company Brain = NCE** (`DEFAULT_TENANT=nextchapter` o. ä.) — First-Party-Nutzung, nicht nur „Dev-Sandbox ohne Gedächtnis“.  

**PROD-VM (Lizenzkunde):** Ubuntu 26.04 Server — nur Compose + Caddy + `license.yaml`.  
→ **eigenes** Company Brain, eigene Volumes — physisch getrennt von NCE-DEV.

```text
NCE DEV-VM (Brain A)     ──✕ kein Auto-Sync──►     Kunden-PROD-VM (Brain B)
Cursor/Antigravity rein                              nur Kunden-Aktivität rein
```

Bootstrap-Befehle: §19 und [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md) § Isolationsmodell.

**Host:** nur KVM/libvirt (z. B. Tuxedo). Kein Hypervisor in der Appliance.  
Ollama Default remote (LAN/Hetzner) — nicht Pflicht in der VM.  
Optional später: zweite NCE-VM „PROD-like“ (ohne Cursor) für eigenen Betrieb — gleiche Isolation.

### 5.5 Datenbank-Schema initialisieren

Aus v1 portieren: `stack/config/init-*.sql`

Neue Tabellen für v2:

```sql
-- Scheduler
CREATE TABLE schedule_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  cron_expr VARCHAR NOT NULL,
  workflow_name VARCHAR NOT NULL,
  delivery_channels JSONB DEFAULT '[]',
  last_run_at TIMESTAMP,
  next_run_at TIMESTAMP,
  enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Workflow-Checkpoints (LangGraph)
CREATE TABLE workflow_checkpoints (
  thread_id VARCHAR NOT NULL,
  checkpoint_id VARCHAR NOT NULL,
  parent_id VARCHAR,
  type VARCHAR,
  checkpoint BYTEA,
  metadata JSONB,
  PRIMARY KEY (thread_id, checkpoint_id)
);

-- Skill-Index
CREATE TABLE skills (
  id VARCHAR PRIMARY KEY,
  tenant_id VARCHAR NOT NULL,
  title VARCHAR NOT NULL,
  description TEXT,
  file_path VARCHAR NOT NULL,
  version INT DEFAULT 1,
  success_rate FLOAT,
  use_count INT DEFAULT 0,
  tags JSONB DEFAULT '[]',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_skills_tenant ON skills(tenant_id);
CREATE INDEX idx_skills_fts ON skills USING gin(to_tsvector('german', title || ' ' || description));

-- Audit hash-chained (P17 — NEU v2, Vorbild Cognithor TRUST-Ledger / Verisa)
-- ai_os_log aus v1 portieren + zwei Spalten ergänzen:
ALTER TABLE ai_os_log ADD COLUMN prev_hash CHAR(64);
ALTER TABLE ai_os_log ADD COLUMN entry_hash CHAR(64) NOT NULL;
-- entry_hash = SHA256(canonical_json(payload) || prev_hash)
-- Verifikation: chain_verify(tenant_id) prüft lückenlose Kette.
CREATE INDEX idx_aioslog_chain ON ai_os_log(tenant_id, created_at);

-- Signierte Run-Receipts (P17 — ein Beleg pro Workflow-Run)
CREATE TABLE run_receipts (
  run_id UUID PRIMARY KEY,
  tenant_id VARCHAR NOT NULL,
  workflow_name VARCHAR NOT NULL,
  cost_micro_usd BIGINT DEFAULT 0,      -- FinOps, P12
  model_calls JSONB DEFAULT '[]',       -- Modell, Tokens, lokal/cloud
  permission_scopes JSONB DEFAULT '[]', -- welche Tools/Scopes genutzt
  cloud_escalations JSONB DEFAULT '[]', -- wann/warum LAN verlassen
  chain_hash CHAR(64) NOT NULL,         -- letzter ai_os_log-Hash des Runs
  signature TEXT NOT NULL,              -- Ed25519 über Receipt-JSON
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_receipts_tenant ON run_receipts(tenant_id, created_at);
```

---

## 6. Phase 1 — Core OS + Memory Gateway

**Dauer:** 1–1.5 Wochen  
**Ziel:** Orchestrator, Workflow-Engine (LangGraph), MCP-Gateway, **Unified Search**, **Memory Gateway** (Model Gateway + Persist-Hook), LangFuse-Tracing, Console-Skeleton — alles **in der Platform-VM**  
**Akzeptanzkriterium:**
- `POST /v1/dispatch {intent: "ping"}` → `{status: "ok", context_bundle: {...}}`
- `POST /v1/search {query: "..."}` → Treffer aus L1 + G + SK + A
- `GET /v1/models` → Liste mit Default `ai-os-sovereign` (Ollama lokal/LAN)
- Jeder LLM-Call über Gateway hinterlässt Memory-Trail + Audit + LangFuse-Trace
- LangFuse zeigt ersten Trace nach Test-Dispatch
- Policy „eine Tür“ dokumentiert (DEV weich / PROD hart: kein direkter Public-LLM-Outbound)
### 6.1 Orchestrator

Port von `stack/orchestrator/server.py` und `stack/scripts/tools/`:

```python
# core/orchestrator/server.py
from fastapi import FastAPI
from .intent_router import route_intent
from .context_resolution import resolve_context
from .dispatch import dispatch
from .audit import write_agent_run

app = FastAPI(title="AI-OS Orchestrator", version="2.0.0")

@app.post("/v1/dispatch")
async def dispatch_intent(req: DispatchRequest):
    intent = route_intent(req.intent, req.params)
    context_bundle = resolve_context(intent, req.tenant_id, req.params)
    result = await dispatch(intent, context_bundle, req.tenant_id)
    write_agent_run(intent, result, req.tenant_id)
    return DispatchResponse(status="ok", result=result)

@app.post("/v1/dataproduct/commit")
async def commit_dataproduct(req: DPCommitRequest):
    # ← v1: dataproduct.py
    ...

@app.post("/v1/context/resolve")
async def resolve_context_endpoint(req: ContextRequest):
    # ← v1: context_resolution.py
    ...

@app.get("/v1/mcp/servers")
async def list_mcp_servers():
    # Delegiert an MCP-Gateway
    ...

@app.post("/v1/mcp/call")
async def call_mcp(req: MCPCallRequest):
    # Delegiert an MCP-Gateway
    ...
```

**Context Resolution — 6 Slices (aus v1 portieren, erweitern):**

```python
# core/orchestrator/context_resolution.py
def resolve_context(intent: str, tenant_id: str, params: dict) -> ContextBundle:
    return ContextBundle(
        system=SystemSlice(     # Tenant, Policies, Brand, Compute-Mode
            tenant=load_tenant_config(tenant_id),
            policies=load_guardrails_config(tenant_id),
        ),
        domain=DomainSlice(     # KG-Traversal 1-2 Hops
            entities=kg_traverse(intent, tenant_id, hops=2),
        ),
        task=TaskSlice(         # Input-DP-Refs, Parameter
            params=params,
            input_refs=params.get("input_dp_refs", []),
        ),
        retrieval=RetrievalSlice(   # L1 Vektor + GraphRAG (Phase 6)
            chunks=qdrant_search(intent, tenant_id, k=5),
        ),
        episodic=EpisodicSlice(     # L2 letzte AgentRuns, User-Modell
            recent_runs=get_recent_runs(tenant_id, limit=3),
            user_model=letta_get_user_model(tenant_id),
        ),
        guardrail=GuardrailSlice(   # Compliance, PII-Grenzen
            policies=get_active_policies(tenant_id),
        ),
        skills=SkillSlice(          # NEU v2: passende Skills
            skills=skill_loader.find_relevant(intent, tenant_id),
        ),
    )
```

### 6.2 Workflow-Engine (LangGraph)

```python
# core/workflow-engine/engine.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict

class WorkflowState(TypedDict):
    tenant_id: str
    context_bundle: dict
    intent: str
    steps_completed: list[str]
    output_dp: dict | None
    error: str | None

def create_workflow(workflow_name: str) -> StateGraph:
    """Lädt Workflow-Definition aus Registry, erstellt LangGraph."""
    definition = load_workflow_definition(workflow_name)
    graph = StateGraph(WorkflowState)

    for step in definition.steps:
        node_fn = load_node_function(step.type, step.agent)
        graph.add_node(step.name, node_fn)

    # Edges aus Definition aufbauen
    for edge in definition.edges:
        if edge.condition:
            graph.add_conditional_edges(edge.from_node, edge.condition_fn)
        else:
            graph.add_edge(edge.from_node, edge.to_node or END)

    # Checkpoint-Store: Postgres
    checkpointer = PostgresSaver.from_conn_string(os.environ["POSTGRES_URL"])
    return graph.compile(checkpointer=checkpointer)

async def run_workflow(workflow_name: str, state: WorkflowState) -> WorkflowState:
    graph = create_workflow(workflow_name)
    thread_id = f"{state['tenant_id']}-{uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}
    result = await graph.ainvoke(state, config=config)
    return result
```

**Deterministic Replay (NEU v2 — Vorbild Synesis):** Jeder Node-Input/-Output wird als Checkpoint + Event in der A-Schicht persistiert. Ein Run lässt sich aus den Checkpoints exakt reproduzieren (`replay_run(thread_id)`) — LLM-Calls werden dabei aus dem aufgezeichneten Trace bedient statt neu ausgeführt. Kernwerkzeug für Debugging und Regressionstests, ergänzt die LangFuse-Traces.

**Workflow-Definition (YAML-Format):**

```yaml
# config/workflows/daily-briefing.yaml
name: daily-briefing
description: Tages-Briefing mit Emails, News und Kalender
version: "2.0"

steps:
  - name: fetch-emails
    type: mcp_call
    server: mail
    tool: get_recent
    params: {max: 10}
    produces: email:EmailBatch

  - name: fetch-calendar
    type: mcp_call
    server: calendar
    tool: get_today
    produces: calendar:DaySchedule

  - name: synthesize
    type: agent_call
    agent: research-agent
    skill: daily-briefing-synthesis
    consumes: [email:EmailBatch, calendar:DaySchedule]
    produces: platform:DailyBriefing

  - name: deliver
    type: mcp_call
    server: console
    tool: push_notification
    consumes: platform:DailyBriefing

edges:
  - {from: fetch-emails, to: synthesize}
  - {from: fetch-calendar, to: synthesize}
  - {from: synthesize, to: deliver}
```

### 6.3 MCP-Gateway

Port von `stack/scripts/tools/mcp_gateway.py` und `mcp_adapters.py`:

```python
# core/mcp-gateway/gateway.py
from fastapi import FastAPI, HTTPException
from .registry import MCPRegistry
from .audit import log_mcp_call

app = FastAPI(title="AI-OS MCP Gateway", version="2.0.0")
registry = MCPRegistry.load("config/mcp-servers.yaml")

@app.post("/v1/call")
async def call_tool(req: MCPCallRequest, tenant_id: str):
    server = registry.get_server(req.server_id)
    if not server.is_allowed_for_tenant(tenant_id):
        raise HTTPException(403, "Server not allowed for tenant")
    if server.over_cap(tenant_id):
        raise HTTPException(429, "Rate cap exceeded")

    result = await server.call(req.tool_name, req.arguments)
    log_mcp_call(req, result, tenant_id)
    return MCPCallResponse(result=result, server_id=req.server_id)
```

**Native Adapter aus v1 portieren** (alle in `stack/scripts/tools/`):
- `mcp_adapters.py` → aufteilen in `adapters/web_search.py`, `adapters/mail.py`, etc.
- Jeder Adapter implementiert `MCPAdapter` Interface mit `call(tool_name, arguments) → dict`

### 6.4 Console Skeleton

Next.js 15 — aus v1 (`stack/console-web/`) portieren, aber mit neuer Routenstruktur:

```
src/app/
├── page.tsx                # Ebene 1: Lagebild (daily summary, alerts)
├── workflows/
│   ├── page.tsx            # Ebene 2: Workflow-Übersicht
│   ├── briefing/page.tsx   # Daily Briefing
│   └── [id]/page.tsx       # Workflow-Detail
└── platform/
    ├── page.tsx            # Ebene 3: Plattform-Übersicht (selten öffnen)
    ├── storage/page.tsx    # Memory-Stacks + VM-Festplatte (Speicherverbrauch)
    ├── mcp/page.tsx        # MCP-Gateway Status
    ├── search/page.tsx     # Unified Search UI (Platform-Kern)
    └── models/page.tsx     # Modellauswahl (Default: lokal)
/context/[runId]/page.tsx   # LLM-Kontext pro Orchestrator-Run (Prompt + Retrieval)
```

### 6.5 Unified Search (Platform-Kern — ab Phase 1)

Jede in der VM erzeugte oder beschaffte Information wird indexiert und ist über **einen** Such-Endpoint auffindbar.  
**Zuerst Query-Router** (P18 / §12.4.7): nur geplante Schichten werden befragt — nie blind L1+G+Letta+SK.

```python
# core/search-service/unified_search.py
@app.post("/v1/search")
async def unified_search(req: SearchRequest) -> SearchResponse:
    """
    1) plan = query_router.plan(req.query, req.intent_hint)  # deterministisch
    2) Quellen nur laut plan (tenant-isoliert), z. B.:
    - G   Postgres KG     wenn plan.use_g
    - L1  Qdrant          wenn plan.use_l1
    - SK  Skill-Store     wenn plan.use_sk
    - A   Audit-Log       wenn plan.use_a
    - K   Datei-Resolve   wenn plan.use_k_resolve (nach Node-ID)
    - Letta gehört nicht in diesen Endpoint — EpisodicSlice separat

    Score-Fusion (Vorbild Synesis/Olla Nest) nur über aktivierte Quellen:
    final = w_vec*vec + w_fts*bm25 + w_graph*graph_centrality + w_recency*decay
    Gewichte pro Tenant konfigurierbar, Default in config/search.yaml.
    Router-Regeln: config/query-router.yaml · Spec: docs/09-COMPANY-BRAIN.md §12.1
    """
    ...
```

**Pflicht-Hook:** Nach jedem `POST /v1/dataproduct/commit` und jedem MCP-Call → `index_hooks.reindex(dp_id)`.

**Score-Fusion statt reines Vektor-Ranking:** Kombiniert Vektor-, BM25-, Graph-Zentralität und Recency zu einem gewichteten Score — deutlich robuster als top-k-Cosine allein.

### 6.6 Memory Gateway = Model Gateway + Persist-Hook (P19 — ab Phase 1)

Das frühere „Model Gateway“ ist in v2 das **Memory Gateway**: dieselbe Tür für Inference **und** Gedächtnis.

```text
Console / Agent / SDK
        │
        ▼
 Memory Gateway  (:4000 LiteLLM + Persist-Hook)
        ├── Inference: Ollama (sovereign) | OpenRouter (balanced/premium)
        └── Pflicht nach jedem Call:
              → L1-Chunk / Episode-Hook (je Policy)
              → A (ai_os_log, hash-chained)
              → LangFuse Trace
              → optional Index-Hook für Unified Search
```

```yaml
# config/compute.yaml — Default: lokal
modes:
  sovereign:
    default_model: ai-os-sovereign    # Ollama qwen3.6-64k (LAN)
    label: "Lokal (LAN)"
  balanced:
    default_model: ai-os-balanced     # OpenRouter nemotron-3-super-120b :free
    label: "Cloud (Free)"
  premium:
    default_model: ai-os-premium      # OpenRouter nemotron-3-ultra-550b :free
    label: "Frontier (Free)"
  coding:
    default_model: ai-os-coding       # OpenRouter poolside/laguna-m.1 :free
    label: "Coding (Free)"
default_mode: sovereign
```

```python
# core/memory-gateway/  (Model Gateway + hooks)
# LiteLLM-Aliase — Start nur mit Ollama; OpenRouter bei Key-Aktivierung
# GET /v1/models → Liste für Console
# POST /v1/compute/mode → Tenant-Modus wechseln (Audit + LangFuse-Tag)
# Nach Completion: persist_chat_turn(tenant, messages, meta) — nie optional in PROD
```

**Start-Konfiguration:** `ai-os-sovereign` (Ollama LAN) ist Default. OpenRouter-Modelle in `litellm-config.yaml` sind vorkonfiguriert (`:free` auf DEV) und werden bei gesetztem `OPENROUTER_API_KEY` für `balanced`/`premium`/`coding` freigeschaltet — **gleicher** Ingest-Hook. Fallback-Kette: balanced/premium/coding → `ai-os-fallback` (`openrouter/free`).

**Sovereign-Pfad (2026-07-26):** Qwen liefert über LiteLLM/OpenAI-kompatibel oft nur `reasoning_content`. Der Memory-Gateway-Client nutzt für `sovereign` deshalb **Ollama `/api/chat` direkt** mit `think: false` — danach LiteLLM-Fallback.

**Policy „eine Tür“:** Kein direkter Outbound zu Public-LLM-APIs aus der VM (DEV: Warnung/Allowlist; PROD: blockiert). Console-Chat nur über Gateway.

**Auto-Router mit Modell-Scoring (Vorbild ArcaQ/Synesis):** Statt fixem Modell pro Modus bewertet der Gateway pro Task-Klasse (Complexity, Context-Länge, benötigte Fähigkeiten) und wählt das günstigste Modell, das den Score-Schwellwert erreicht. Lokal gewinnt bei Gleichstand (P12).

**CAG — Cache-Augmented Generation (Vorbild Olla Nest):** Wiederkehrende System-Prompts + stabile Kontext-Slices werden als KV-Cache-Präfix gehalten. Spart Tokens und Latenz bei häufig genutzten Platform-Prompts. Aktiv für `sovereign` (Ollama `keep_alive` + Prompt-Präfix-Cache).

**Implementierungsstand (2026-07-26):**

| Baustein | Status |
|----------|--------|
| `core/memory_gateway/` (client, persist, audit, langfuse_hook) | ✅ |
| `config/compute.yaml` (sovereign/balanced/premium/coding) | ✅ |
| Orchestrator `GET /v1/models` + `POST /v1/chat/completions` | ✅ |
| **`GET/POST /v1/compute/mode`** — persistiert in `compute-mode.json` | ✅ |
| **Console ComputeModePanel** — aktives Modell im Lagebild | ✅ |
| **Sovereign Ollama direkt** (`think: false`) + LiteLLM-Fallback | ✅ |
| **OpenRouter Free** — Nemotron Super/Ultra, Laguna Coding, Fallback | ✅ |
| Persist-Hook → `memory.db` + `ai_os_log` Hash-Chain | ✅ |
| LangFuse-Trace (optional bei gesetzten Keys) | ✅ Hook, Keys oft leer auf DEV |
| `memory_ask` + Console `memory-ask.ts` über Gateway | ✅ |
| **`memory_ask` DE-Antwortbereinigung** — Thinking-Leaks, Retry | ✅ |
| LiteLLM-Primary + Ollama-Fallback (Cloud-Modi) | ✅ |
| Letta L2 (`letta_client.py`) + SQLite-Backfill/Sync | ✅ |
| Episodische Suche merged (`episodic_search.py`) + `POST /v1/search` | ✅ |
| **L2-Curator** Tagesdigest → Letta (`core/memory/l2_curator.py`, tägl. 02:00) | ✅ |
| **L3-Curator** Fakten → `org:Claim` + Letta Core (`core/memory/l3_curator.py`) | ✅ |
| **L1-Curator** Qdrant Dedup + Rolling 90d (`core/memory/l1_curator.py`, So 03:00) | ✅ |
| **Working/Tactical-Memory** + Run-Destillation P9 (`run_distill.py`, Dispatch-Hook) | ✅ |
| **Lagebild `memory_ask` federiert** — Projektstand via Graph + L1 (nicht nur Letta); Active-Projekt-Erkennung | ✅ |
| **Intent „Was steht heute an“** → `daily_open_loops` (Brain-Engagements + Kalender) | ✅ |
| **Run-Context-Store** — LLM-Prompt + Retrieval pro Run (`run_context_store.py`, `GET /v1/runs/{id}/context`) | ✅ |
| Console **Speicher-Dashboard** (`/platform/storage`, `GET /v1/memory/storage`) | ✅ |
| Console **LLM-Kontext-Link** im Lagebild (`/context/{runId}`) — Governance-Basis für Fachagenten/Cloud | ✅ |
| **Memory-Testcases** (`testcases/memory/`, `scripts/run-memory-testcases.py`, 70+ Cases) | ✅ |
| **Compute-Testcases** (`testcases/compute/`, `scripts/run-compute-mode-testcases.py`, 14 Cases) | ✅ |
| L3 Human-Gate UI (Pending-Claims in Console) | ⏳ |
| Auto-Router / CAG / PROD-Outbound-Block | ⏳ Phase 1+ |
| Coding-Modus nur für Code-Tasks (Routing-Guard) | ⏳ |

**Nächster Roadmap-Punkt:** Phase 2 — Platform-Agenten-Laufzeit + Platform-Gate (§7); Compute-Modi + Lagebild-Tagesfrage ✅.

### 6.8 Lagebild — federierter Ask + LLM-Kontext (2026-07-25)

**Problem:** Lagebild-Fragen (`memory_ask`) lasen nur episodisches Letta — ROADMAP/Knowledge Assets in Graph+L1 blieben unsichtbar.

**Lösung:**

```text
Frage im Lagebild
    │
    ├─ _needs_federated_context?  (Stand/Status/Roadmap, Active-Projekt-Slug)
    │       ja → Unified Search (Graph + L1 content + raw-files) + wenig Letta
    │       nein → nur episodisch (Letta/SQLite)
    │
    ├─ Prompt bauen (System + User mit Chunks, max ~5500 Zeichen)
    ├─ Ollama via Memory Gateway
    └─ Run-Context speichern → GET /v1/runs/{run_id}/context
```

**Zwei Kontext-Ebenen (wichtig für spätere Fachagenten):**

| Ebene | Was | Wo sichtbar |
|-------|-----|-------------|
| **Orchestrator Context Bundle** | 6–7 Slices (System, Domain, Task, Retrieval, Episodic, Guardrail, Skill) — *vor* dem Handler | `/context/{runId}` → „Orchestrator Context Bundle“ |
| **LLM-Prompt-Kontext** | Was tatsächlich ans Modell geht: System-Prompt + Frage + Retrieval-Chunks | `/context/{runId}` → System/User-Prompt + Retrieval |

Persistenz: `AIOS_RUN_CONTEXT_DIR` (Default `/opt/ai-os/memory/state/run-context/{runId}.json`).  
Routing-Metadaten enthalten `modelTier: local` — später `cloud` / `agent` für Public-Modelle.  
**Ausführlich (menschlich):** [docs/14-KONTEXT.md](docs/14-KONTEXT.md)

### 6.9 Compute-Modi im Lagebild + Tagesfrage (2026-07-26)

**Console:** `ComputeModePanel` auf dem Lagebild — zeigt aktiven Modus/Modell, Umschalten via `POST /v1/compute/mode` (Orchestrator), persistiert unter `AIOS_COMPUTE_MODE_PATH`.

**Intent-Routing Tagesfrage:**

```text
„Was steht heute an“ / „steht heute an“ / „was steht an“
    → daily_open_loops (Brain-Engagements, Termine, Mails)
    → strukturierte DE-Antwort aus Seed/Brain — unabhängig vom UI-Modus
    → Hintergrund-Memory-Snippet immer sovereign (lokal, kurz)
```

**memory_ask** (Wissensfragen im Lagebild): nutzt den gewählten Compute-Modus; Sovereign über Ollama direkt; Cloud/Coding mit DE-Prompt + `_clean_answer()` gegen Thinking-Leaks. **Coding** ist für agentic Code — allgemeine Lagebild-Fragen → Balanced/Frontier oder `daily_open_loops`.

**Regression:** `python3 scripts/run-compute-mode-testcases.py` — 14 Cases (Modus-API, LiteLLM-Routing, Intent, Overrides).

### 6.7 LangFuse-Tracing (ab Phase 1 — Pflicht)

Jeder LLM-Call und jeder LangGraph-Node sendet Traces an lokales LangFuse (`http://langfuse:3000`). Kein Cloud-Callback.

**Akzeptanztest Phase 1:**

```bash
# Infra + Monitoring
docker compose -f deploy/infra.yml -f deploy/monitoring.yml up -d

# Core starten
docker compose -f deploy/core.yml up -d

# Health
curl http://localhost:8091/health           # → {"status": "ok"}
curl http://localhost:3000/api/public/health # → LangFuse OK

# Dispatch + Trace
curl -X POST http://localhost:8091/v1/dispatch \
  -H 'Content-Type: application/json' \
  -d '{"intent": "ping", "tenant_id": "platform-test"}'

# Unified Search (Orchestrator)
curl -X POST http://localhost:8091/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "Memory Gateway", "tenant_id": "nextchapter"}'

# L2/L3 Curator (manuell)
python3 scripts/run-l2-curator.py --dry-run
python3 scripts/run-l3-curator.py --dry-run

# Memory Gateway — Default lokal
curl http://localhost:8091/v1/models        # → ai-os-sovereign (default)

# Console
curl http://localhost:8092                # → HTML
```

---

## 6b. Phase 1b — Chat Capture (externe Chats ins Gedächtnis)

**Dauer:** ~1 Woche (kann mit Ende Phase 1 überlappen)  
**Ziel:** Chats aus Gemini, Antigravity (und ChatGPT-Export) landen im **selben** Speicher wie Platform-Chats  
**Spec:** [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md) · v1-Port: `chat_import` / Antigravity-Import  
**Compose:** `deploy/chat-capture.yml`

| # | Deliverable | Akzeptanz |
|---|-------------|-----------|
| 1b.1 | **Chat Capture Service** in der VM | Ersetzt v1 Host-Poller; schreibt nach Inbox / ruft `/v1/chat-import` |
| 1b.2 | **Gemini-Import** | Drive-/Export-Datei → normalisiert → L1 + L2 (+ Audit) |
| 1b.3 | **Antigravity-Import** | `transcript.jsonl` oder Inbox-Markdown aus DEV-VM → gleicher Pfad |
| 1b.4 | **ChatGPT-Export** | JSON-Export → derselbe Normalizer |
| 1b.5 | Console „Chat-Erfassung“ | Status, letzter Import, manueller Upload |
| 1b.6 | Abgrenzung P18 | Roh-Chat ≠ `org:Claim`; Claims nur L3-Curator / DP-Commit |

**DoD Phase 1b:** Ein Gemini- oder Antigravity-Chat von gestern ist heute über Unified Search / Orchestrator auffindbar — unabhängig von der Quelle — **auf derselben VM** (NCE-DEV → NCE-Brain).

```text
Gemini / Antigravity / ChatGPT-Export
        → chat-capture (diese VM)
        → POST /v1/chat-import
        → SQLite L1 (FTS) + L2 Letta Archival + Audit
        → L2-Curator (tägl.) → Tagesdigest in Letta
        → L3-Curator (wöch.) → org:Claim via DP-Commit (Human-Gate bei supports_refs)
```

**Nicht:** Capture von NCE-DEV in eine Kunden-PROD-DB schreiben.

**Implementierungsstand (2026-07-25):**

| Baustein | Status |
|----------|--------|
| `POST /v1/chat-import` + `core/orchestrator/chat_import.py` | ✅ |
| Antigravity-Poller `core/capture/antigravity-job.mjs` + systemd | ✅ |
| Gemini-Inbox-Poller `core/capture/gemini-inbox-job.mjs` + systemd | ✅ |
| Console `/platform/capture` (Chat-Erfassung) | ✅ |
| `GET /v1/capture/stats` | ✅ |
| `deploy/chat-capture.yml` (Docker optional) | ✅ Scaffold |
| ChatGPT-Export-Parser | ⏳ |
| Drive-Poller Gemini (v1 C2) | ⏳ |
| Letta Live-Sync (Cursor → L2) + Backfill | ✅ |
| `POST /v1/memory/sync-letta` · `rebuild-fts` | ✅ |

**Nächster Roadmap-Punkt:** Phase 2 — Platform-Agenten-Laufzeit + Platform-Gate (§7); Memory-Curators L1/L2/L3 ✅, Working/Tactical ✅.

---

## 7. Phase 2 — Platform-Agenten

**Dauer:** 1–1.5 Wochen  
**Ziel:** Alle Platform-Agenten laufen, Scheduler produktiv, **P9 Datenpersistenz durchgängig**, Platform-Gate bestanden  
**Akzeptanzkriterium:** `daily-briefing`-Workflow läuft durch, Skill-Loop erzeugt Skill-Dokument, **alle Outputs in DB**

### 7.0 Datenpersistenz-Regel (P9 — gilt für alle Platform-Agenten)

Jeder Schritt, der Daten erzeugt oder beschafft, **muss** vor Workflow-Ende committen:

| Quelle | Pflicht-Ziele |
|--------|---------------|
| MCP-Call (mail, web, calendar …) | `A` (Audit) + `G` (KG-Knoten) + ggf. `L1` |
| Agent-Output | `G` + typisiertes DP in Postgres |
| Skill-Destillation | `SK` + `G` |
| LLM-Antwort (relevant) | DP-Commit oder Archival `L2` |
| Datei-Ingest | `K` + `L1` + DP-Commit |

**Verboten:** Daten nur im Workflow-State (RAM) oder nur in LangFuse — LangFuse ist Observability, nicht Speicher.

### 7.0.1 Platform-Gate (⛔ Pflicht vor Phase 4)

```bash
# Alle Checks müssen PASS sein, bevor ein Fach-Agent deployt wird:
python -m tests.platform_gate --tenant platform-test

# Prüft:
# GATE-01  Infra + LangFuse healthy
# GATE-02  POST /v1/dispatch → Audit-Eintrag in A
# GATE-03  POST /v1/search → Treffer nach DP-Commit
# GATE-04  GET /v1/models → sovereign default
# GATE-05  daily-briefing Workflow E2E (ohne Fach-Agenten)
# GATE-06  Scheduler-Job angelegt + ausgeführt
# GATE-07  Skill-Loop: Skill in SK + suchbar
# GATE-08  Jeder MCP-Call in A + G
# GATE-09  LangFuse: Trace pro Workflow-Run sichtbar
# GATE-10  Memory-Curator: L2-Eintrag nach 24h-Simulation
# GATE-11  PGE-Gatekeeper (P15): RED-Tool geblockt, ORANGE → HITL, GREEN auto
# GATE-12  Observer (P16): injizierte Halluzination wird erkannt + geflaggt
# GATE-13  Audit-Chain (P17): chain_verify() PASS, run_receipt signiert + verifizierbar
# GATE-CB-01..08  Company Brain (P18) — Schema, Seed, Abnahmefragen, Query-Router,
#                 Claim-Härte, atomarer G+K-Commit · §12.4.5–12.4.7 · docs/09 §12
# GATE-14  Redaction-Gateway: PII verlässt LAN nur als Platzhalter (balanced-Test)
```

### 7.1 Pipeline-Agent

Port von `stack/scripts/pipeline.py` — **wichtig:** als SDK-konformer Agent reimplementieren:

```python
# platform-agents/pipeline-agent/agent.py
from sdk.agent_base import AgentBase
from sdk.dataproduct import DataProduct

class PipelineAgent(AgentBase):
    agent_id = "pipeline-agent"
    version = "2.0.0"

    async def run(self, input_dp: DataProduct, context: ContextBundle) -> DataProduct:
        # 7-Schritt-RAG-Pipeline (aus v1)
        # Schritt 1: Query verstehen
        # Schritt 2: L1 Search
        # ...
        return ResearchResult(
            tenant_id=context.system.tenant.id,
            produced_by=self.agent_id,
            # ...
        )
```

### 7.2 Ingest-Agent

Port von `stack/ingest-worker/` — hauptsächlich Inbox-Polling → Qdrant-Indexierung.

> **Nicht verwechseln mit:** `core/file_ingest_watcher/` — ein vorgezogener,
> bewusst provisorischer Übergangs-Dienst (Bridge bis Fach-Agenten stehen),
> der rohe Projektdateien in eine separate Collection `raw-files` indexiert,
> **ohne** DP-Commit/Company-Brain-Anbindung. Siehe
> [ADR 0002](docs/adr/0002-file-ingest-watcher-und-rolle-von-cursor.md).
> Der hier beschriebene Ingest-Agent (Phase 2) bleibt der Ziel-Weg mit
> DP-Commit ins Company Brain.

Neue Funktion: **DP-Commit nach Ingest** (in v1 war das implizit):

```python
# Nach erfolgreicher Indexierung immer:
dp = IngestDocument(
    tenant_id=tenant_id,
    source_path=file_path,
    indexed_at=datetime.now(),
    chunk_count=len(chunks),
    qdrant_ids=chunk_ids,
)
await orchestrator_client.commit_dataproduct(dp)
```

### 7.3 Memory-Agent

Implementiert L1/L2/L3-Curators + Kurzzeit-Ebenen — **größtenteils neu in v2**:

**Working- + Tactical-Memory (NEU v2 — Vorbild Synesis):** Zusätzlich zu den persistenten L1–L3-Ebenen führt jeder Run ein flüchtiges **Working-Memory** (aktueller Task-Scratchpad) und ein **Tactical-Memory** (Zwischenergebnisse über mehrere Schritte eines Workflows). Beide werden am Run-Ende gemäß P9 in die persistenten Ebenen destilliert — nie einfach verworfen.

```python
# core/memory/l1_curator.py — aus v1 portieren
# core/memory/l2_curator.py — NEU: verdichtet L1-Episoden → Letta
# core/memory/l3_curator.py — NEU: extrahiert Fakten → KG
# core/memory/working_memory.py  — NEU: Run-Scratchpad (flüchtig)
# core/memory/tactical_memory.py — NEU: Multi-Step-Zwischenstand (flüchtig)
# Beide → am Run-Ende Destillation in L1/L2/L3 (P9)

class L2Curator:
    """Verdichtet L1-Chunks zu episodischen Erinnerungen in Letta."""
    async def curate(self, tenant_id: str):
        # 1. Qdrant: Chunks der letzten 24h laden
        recent = await qdrant.get_recent(tenant_id, hours=24)
        # 2. LLM: Zusammenfassung als Episode
        episode = await llm.summarize_as_episode(recent)
        # 3. Letta: Episode speichern
        await letta.add_archival_memory(tenant_id, episode)
        # 4. DP committen
        await dp_client.commit(EpisodicMemoryCreated(...))

class L3Curator:
    """Extrahiert stabile Fakten aus L2 → OrgClaim DataProduct → DP-Commit → G.
    Kein Direkt-Write in kg_*; confidence-Threshold aus Config (Default 0.7).
    Siehe P18 / docs/09-COMPANY-BRAIN.md."""
    async def curate(self, tenant_id: str):
        # 1. Letta: neue Episoden der letzten 7 Tage
        episodes = await letta.get_archival_memory(tenant_id, days=7)
        # 2. LLM: Fakten + Entitäten extrahieren
        facts = await llm.extract_facts(episodes)
        # 3. KG: upsert_node + add_edge für jedes Fakt
        for fact in facts:
            await kg.upsert_fact(fact, tenant_id)
```

**Implementierungsstand (2026-07-25):**

| Baustein | Status |
|----------|--------|
| `core/memory/l2_curator.py` — SQLite 24h → Tagesdigest → Letta L2 | ✅ |
| `core/memory/l3_curator.py` — L2 → `org:Claim` + Letta Core | ✅ |
| `config/memory-curator.yaml` | ✅ |
| `POST /v1/memory/curate/l2` · `POST /v1/memory/curate/l3` | ✅ |
| `GET /v1/memory/curate/l3/pending` (Human-Gate API) | ✅ |
| systemd `aios-l2-curator.timer` (02:00) · `aios-l3-curator.timer` (So 04:00) | ✅ |
| `core/memory/l1_curator.py` (Qdrant rolling) | ✅ |
| `working_memory.py` / `tactical_memory.py` | ✅ |
| `run_distill.py` — Run-Ende → Letta L2 oder Audit (P9) | ✅ |
| `POST /v1/memory/curate/l1` · `GET /v1/memory/l1/stats` | ✅ |
| `GET /v1/memory/working/{run_id}` · `GET /v1/memory/tactical/{wf}` | ✅ |
| systemd `aios-l1-curator.timer` (So 03:00) | ✅ |
| Console Decision-Inbox / Claim-Gate UI | ⏳ |

### 7.4 Guardrails-Agent

Port von v1 + **L3 PII-Filter neu implementieren**:

```python
# platform-agents/guardrails-agent/pii_scanner.py — NEU L3
class PIIScanner:
    PATTERNS = {
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "iban": r'[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}',
        "phone_de": r'(\+49|0)[1-9]\d{1,14}',
    }

    def scan(self, text: str) -> PIIScanResult:
        findings = []
        for pii_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                findings.append(PIIFinding(type=pii_type, count=len(matches)))
        return PIIScanResult(findings=findings, blocked=len(findings) > 0)
```

**Redaction-Gateway vor Cloud (NEU v2 — Vorbild ArcaQ):** Bei `balanced`/`premium` läuft jeder Prompt vor Verlassen des LAN durch einen Redaktions-Schritt: PII → reversible Platzhalter (`⟦PERSON_1⟧`), nach der Cloud-Antwort Rück-Substitution. Der Cloud-Provider sieht nie Klartext-PII. Bei `sovereign` deaktiviert (Daten bleiben im LAN).

```python
# platform-agents/guardrails-agent/redaction_gateway.py — NEU v2
class RedactionGateway:
    def redact(self, text: str, tenant_id: str) -> tuple[str, RedactionMap]:
        """PII → reversible Tokens, Map nur lokal (nie an Cloud)."""
        ...
    def restore(self, text: str, rmap: RedactionMap) -> str:
        """Cloud-Antwort → Klartext zurück (nur im LAN)."""
        ...
```

### 7.4a PGE-Gatekeeper (NEU v2 — P15, Platform-Kern)

Der Gatekeeper ist **deterministischer Code** zwischen Planner (LLM) und Executor. Er ist die konkrete Umsetzung von P4 und der Guardrails.

```python
# core/orchestrator/gatekeeper.py — NEU v2
class Gatekeeper:
    """Validiert jeden geplanten Tool-Call VOR Ausführung. Kein LLM."""
    RISK = {"read_kg": "GREEN", "web_fetch": "YELLOW",
            "send_email": "ORANGE", "shell_exec": "RED"}

    async def check(self, plan: ToolCallPlan, ctx: TenantContext) -> Verdict:
        # 1. Risk-Klasse → GREEN auto, YELLOW policy, ORANGE HITL, RED block
        # 2. Policy-Match (tenant, scope, rate-limit)
        # 3. PII-Scan der Argumente (Redaction-Gateway)
        # 4. Verdict → allow | require_approval | deny  (+ Audit-Eintrag)
        ...
```

**Fluss pro Agent-Run (PGE-Trinity):** `Planner (LLM) → Gatekeeper (Code) → Executor (sandboxed)`. Jeder Verdict landet in der A-Schicht (P17).

### 7.4b Observer Audit Layer (NEU v2 — P16)

```python
# core/orchestrator/observer.py — NEU v2
class ObserverAudit:
    """Post-Response-Qualitätscheck mit LOKALEM Modell (kostenlos)."""
    CHECKS = ["hallucination", "sycophancy", "laziness", "tool_ignorance"]

    async def review(self, run: AgentRun) -> ObserverVerdict:
        # Lokales Modell prüft Antwort gegen Kontext + Tool-Ergebnisse.
        # Verstoß → regenerate | re_loop | flag. Fail-open (nie blockieren).
        ...
```

Läuft deterministisch getriggert nach jeder Agent-Antwort, nutzt ausschließlich `ai-os-sovereign` → keine zusätzlichen Cloud-Kosten.

### 7.5 Scheduler-Agent (NEU — war P2-Blocker in v1)

```python
# core/scheduler/scheduler_service.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class SchedulerService:
    def __init__(self, orchestrator_client, db):
        self.scheduler = AsyncIOScheduler()
        self.orchestrator = orchestrator_client
        self.db = db

    async def start(self):
        # Alle aktiven Jobs aus DB laden
        jobs = await self.db.get_active_jobs()
        for job in jobs:
            self.scheduler.add_job(
                self._run_job,
                CronTrigger.from_crontab(job.cron_expr),
                args=[job],
                id=str(job.id),
            )
        self.scheduler.start()

    async def _run_job(self, job: ScheduleJob):
        result = await self.orchestrator.dispatch(
            intent=job.workflow_name,
            tenant_id=job.tenant_id,
            params={"triggered_by": "scheduler", "job_id": str(job.id)},
        )
        # Delivery an konfigurierte Kanäle
        for channel in job.delivery_channels:
            await self._deliver(result, channel, job.tenant_id)
        await self.db.update_last_run(job.id)

# Natural-Language → Cron
class NaturalLanguageCronParser:
    MAPPINGS = {
        "täglich 7 uhr": "0 7 * * *",
        "jeden morgen": "0 7 * * *",
        "wöchentlich montag": "0 9 * * 1",
        "stündlich": "0 * * * *",
    }

    def parse(self, expression: str) -> str:
        expr_lower = expression.lower()
        for pattern, cron in self.MAPPINGS.items():
            if pattern in expr_lower:
                return cron
        # LLM-Fallback für komplexe Ausdrücke
        return self._llm_parse(expression)
```

### 7.6 Skill-Service (NEU)

```python
# core/skill-service/skill_store.py
class SkillStore:
    """Verwaltet Skill-Dokumente: Markdown + Qdrant + FTS5."""

    def save_skill(self, skill: Skill, tenant_id: str):
        # 1. Markdown-Datei schreiben
        path = f"customers/{tenant_id}/skills/{skill.id}.md"
        write_skill_markdown(path, skill)
        # 2. Qdrant: Embedding des title + description
        qdrant.upsert(collection="skills", id=skill.id,
                      vector=embed(f"{skill.title} {skill.description}"),
                      payload={"tenant_id": tenant_id, "path": path})
        # 3. SQLite FTS5: Volltext-Index
        db.execute("INSERT OR REPLACE INTO skills VALUES (?, ?, ?, ?)",
                   [skill.id, tenant_id, skill.title, skill.description])

    def find_relevant(self, intent: str, tenant_id: str, k: int = 3) -> list[Skill]:
        # Hybrid: Vektor + FTS5
        vector_hits = qdrant.search("skills", embed(intent),
                                     filter={"tenant_id": tenant_id}, limit=k)
        fts_hits = db.execute(
            "SELECT id FROM skills WHERE tenant_id=? AND skills MATCH ?",
            [tenant_id, intent]).fetchall()
        return merge_and_rank(vector_hits, fts_hits)

# core/skill-service/skill_distiller.py
class SkillDistiller:
    """Nach komplexem Task: Ablauf → Skill-Dokument destillieren."""

    async def distill(self, agent_run: AgentRun, tenant_id: str) -> Skill | None:
        if not agent_run.is_complex_enough():  # Heuristik: >3 Steps, >30s
            return None

        prompt = f"""
Du analysierst einen abgeschlossenen KI-Task und destillierst ein wiederverwendbares Skill-Dokument.

Task: {agent_run.intent}
Schritte: {agent_run.steps_summary}
Ergebnis: {agent_run.outcome}
Besonderheiten: {agent_run.notes}

Erstelle ein Skill-Dokument im Format:
---
id: <kebab-case-id>
title: <prägnanter Titel>
version: 1
use_when:
  - <Bedingung 1>
  - <Bedingung 2>
---
## Ablauf
1. ...
## Bekannte Fallstricke
- ...
"""
        skill_md = await llm.complete(prompt)
        return Skill.from_markdown(skill_md, tenant_id=tenant_id)
```

---

## 8. Phase 3 — Agent-SDK & Contract

**Dauer:** 3–5 Tage  
**Ziel:** SDK vollständig, alle Platform-Agenten auf SDK migriert, Contract-Tests grün  
**Akzeptanzkriterium:** `python -m pytest sdk/tests/` → 100 % grün

### 8.1 AgentBase — Die Basisklasse

```python
# sdk/agent_base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import TypeVar, Generic
from .dataproduct import DataProduct
from .tenant_context import TenantContext
from .mcp_adapter import MCPAdapter
from .skill_hook import SkillHook

InputDP = TypeVar("InputDP", bound=DataProduct)
OutputDP = TypeVar("OutputDP", bound=DataProduct)

class AgentBase(ABC, Generic[InputDP, OutputDP]):
    """
    Basisklasse für alle AI-OS-Agenten.

    Contract:
    - Input:  typisiertes DataProduct (oder None für trigger-based agents)
    - Output: typisiertes DataProduct
    - Tools:  ausschließlich über self.mcp (MCPAdapter)
    - Kontext: self.ctx (TenantContext) — immer explizit
    - Skills:  self.skill_hook.post_run() nach jedem komplexen Task

    Verletzung des Contracts → ValueError bei Instanziierung.
    """

    agent_id: str           # Muss überschrieben werden
    version: str            # Semantic Versioning
    input_schema: type[InputDP]     # Muss überschrieben werden
    output_schema: type[OutputDP]   # Muss überschrieben werden

    def __init__(self, ctx: TenantContext, mcp: MCPAdapter, skill_hook: SkillHook):
        self._validate_contract()
        self.ctx = ctx
        self.mcp = mcp
        self.skill_hook = skill_hook

    def _validate_contract(self):
        if not hasattr(self, 'agent_id') or not self.agent_id:
            raise ValueError(f"{self.__class__.__name__}: agent_id fehlt")
        if not hasattr(self, 'input_schema'):
            raise ValueError(f"{self.__class__.__name__}: input_schema fehlt")
        if not hasattr(self, 'output_schema'):
            raise ValueError(f"{self.__class__.__name__}: output_schema fehlt")

    @abstractmethod
    async def run(self, input_dp: InputDP) -> OutputDP:
        """Kernlogik des Agenten. Darf nur self.mcp für externe Calls nutzen."""
        ...

    async def execute(self, input_dp: InputDP) -> OutputDP:
        """Wrapper: Contract-Check + run() + Skill-Hook + DP-Commit."""
        # Input validieren
        validated_input = self.input_schema.model_validate(input_dp)

        # Agenten-Logik
        result = await self.run(validated_input)

        # Output validieren
        validated_output = self.output_schema.model_validate(result)

        # DP committen
        await self.ctx.dp_client.commit(validated_output)

        # Observer Audit Layer (P16) — lokal, kostenlos
        await self.ctx.observer.review(validated_input, validated_output)

        # Skill-Hook: Skill destillieren wenn komplex
        await self.skill_hook.post_run(
            agent_id=self.agent_id,
            input_dp=validated_input,
            output_dp=validated_output,
        )

        return validated_output
```

**`_safe_call()`-Konvention (NEU v2 — Vorbild Cognithor):** Kein stilles `except: pass`. Jeder externe Call (MCP, DB, LLM) läuft durch einen einheitlichen Wrapper mit Retry, Timeout, Circuit-Breaker und einer Failure-Registry pro Funktion. Fehler werden strukturiert in die A-Schicht geschrieben, nie verschluckt.

```python
# sdk/safe_call.py — NEU v2
async def _safe_call(fn, *args, registry: FailureRegistry, **kw):
    """Retry + Timeout + Circuit-Breaker. Fehler → Audit, nie stilles pass."""
    ...
```

### 8.2 DataProduct — Basis-Schema

```python
# sdk/dataproduct.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

class DataProduct(BaseModel):
    """Basis für alle typisierten Datenprodukte in AI-OS."""

    # Pflichtfelder — von AgentBase automatisch gesetzt
    dp_id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: str = "1.0"
    tenant_id: str
    produced_by: str                  # Agent-ID
    produced_at: datetime = Field(default_factory=datetime.utcnow)
    workflow_run_id: str | None = None

    # Speicher-Hint (aus platform-storage-rules.yaml)
    storage_target: list[str] = []    # ["L1", "G", "K"] etc.
    ingest_recommended: bool = False

    class Config:
        extra = "forbid"  # Keine undeklarierten Felder

    def to_commit_request(self) -> dict:
        """Für POST /v1/dataproduct/commit."""
        return {
            "node_type": self.__class__.__qualname__,
            "external_id": self.dp_id,
            "tenant_id": self.tenant_id,
            "produced_by": self.produced_by,
            "payload": self.model_dump(),
        }
```

### 8.3 Contract-Tests

```python
# sdk/tests/test_contract.py
import pytest
from sdk.agent_base import AgentBase
from sdk.dataproduct import DataProduct

class ValidInputDP(DataProduct):
    query: str

class ValidOutputDP(DataProduct):
    result: str

class ValidAgent(AgentBase):
    agent_id = "test-agent"
    version = "1.0.0"
    input_schema = ValidInputDP
    output_schema = ValidOutputDP

    async def run(self, input_dp: ValidInputDP) -> ValidOutputDP:
        return ValidOutputDP(
            tenant_id=input_dp.tenant_id,
            produced_by=self.agent_id,
            result=f"processed: {input_dp.query}"
        )

def test_valid_agent_instantiates(mock_ctx, mock_mcp, mock_skill_hook):
    agent = ValidAgent(mock_ctx, mock_mcp, mock_skill_hook)
    assert agent.agent_id == "test-agent"

def test_agent_without_agent_id_fails(mock_ctx, mock_mcp, mock_skill_hook):
    class BrokenAgent(AgentBase):
        input_schema = ValidInputDP
        output_schema = ValidOutputDP
        async def run(self, input_dp): return None

    with pytest.raises(ValueError, match="agent_id fehlt"):
        BrokenAgent(mock_ctx, mock_mcp, mock_skill_hook)

def test_agent_without_output_schema_fails(mock_ctx, mock_mcp, mock_skill_hook):
    class BrokenAgent(AgentBase):
        agent_id = "broken"
        input_schema = ValidInputDP
        async def run(self, input_dp): return None

    with pytest.raises(ValueError, match="output_schema fehlt"):
        BrokenAgent(mock_ctx, mock_mcp, mock_skill_hook)

@pytest.mark.asyncio
async def test_execute_commits_dp(mock_ctx, mock_mcp, mock_skill_hook):
    agent = ValidAgent(mock_ctx, mock_mcp, mock_skill_hook)
    input_dp = ValidInputDP(tenant_id="test", produced_by="console", query="hello")
    result = await agent.execute(input_dp)
    assert result.result == "processed: hello"
    mock_ctx.dp_client.commit.assert_called_once()
```

---

## 9. Phase 4 — Fach-Agenten

**Dauer:** 1.5–2 Wochen  
**Voraussetzung:** ⛔ **Platform-Gate (Kap. 7.0.1) muss PASS sein** — kein Fach-Agent vorher  
**Ziel:** Research, Blog, Email, **Kommunikationsmanager** als SDK-konforme Agenten  
**Akzeptanzkriterium:** alle Contract-Tests grün + E2E-Test für Blog-Workflow; Kommunikationsmanager: Teilnehmerliste → `org:Person`/`org:Meeting` nur via MCP + DP-Commit

> **Regel:** Fach-Agenten sind SKU-Pakete, die auf der laufenden Platform aufsetzen.
> Sie implementieren keine eigene Suche, kein eigenes Monitoring, kein eigenes Modell-Routing.
> Alles über Platform-Services: `/v1/search`, Model Gateway, LangFuse, MCP-Gateway.

> **Standard-Workflow-Muster (NEU v2 — Vorbild Cognithor/Synesis):**
> Content-produzierende Fach-Agenten folgen `Planner → Retrieval → Writer → Critic`:
> 1. **Planner** (LLM) zerlegt die Aufgabe in Schritte.
> 2. **Retrieval** über Unified Search (kein eigener Index).
> 3. **Writer** (LLM) erzeugt Entwurf.
> 4. **Critic-Node** (LLM, lokal) bewertet gegen Kriterien + Quellen; bei Fail → Re-Loop (max. N).
> Der Critic ist Teil des LangGraph-Graphen (P7), der Observer (P16) prüft zusätzlich global.

### 9.0 Fach-Agent aktivieren (nur nach Gate)

```bash
# Erst Platform-Gate prüfen
python -m tests.platform_gate --tenant platform-test  # → 10/10 PASS

# Dann einzelnes Paket
python -m core.packages install --tenant nextchapter --package research-agent
docker compose -f deploy/agents/research.yml up -d
```

### 9.1 Research-Agent

Port von `packages/research-agent/` — **als SDK-konformer Agent reimplementieren**:

```python
# agents/research/agent.py
from sdk.agent_base import AgentBase

class ResearchInput(DataProduct):
    query: str
    depth: Literal["quick", "deep"] = "quick"
    tenant_id: str
    produced_by: str

class ResearchResult(DataProduct):
    query: str
    summary: str
    sources: list[str]
    confidence: float
    tenant_id: str
    produced_by: str

class ResearchAgent(AgentBase):
    agent_id = "research-agent"
    version = "2.0.0"
    input_schema = ResearchInput
    output_schema = ResearchResult

    async def run(self, input_dp: ResearchInput) -> ResearchResult:
        # 1. Web-Suche via MCP
        search_results = await self.mcp.call("web_search", "search",
                                             {"q": input_dp.query, "num": 5})
        # 2. L1-Suche via MCP
        vector_results = await self.mcp.call("qdrant_search", "search",
                                              {"q": input_dp.query, "k": 3,
                                               "tenant_id": self.ctx.tenant_id})
        # 3. Synthesize
        synthesis = await self._synthesize(input_dp.query, search_results, vector_results)
        return ResearchResult(
            tenant_id=self.ctx.tenant_id,
            produced_by=self.agent_id,
            query=input_dp.query,
            summary=synthesis.text,
            sources=synthesis.sources,
            confidence=synthesis.confidence,
        )
```

### 9.2 Blog-Agent

```python
# agents/blog/agent.py
class BlogDraftInput(DataProduct):
    research_ref: str          # DP-ID eines ResearchResult
    target_format: str         # "linkedin" | "blog" | "newsletter"
    style_ref: str | None      # Skill-ID für Stil-Referenz

class BlogDraft(DataProduct):
    title: str
    body: str
    teaser: str | None
    word_count: int
    research_ref: str
    compliance_status: Literal["pending", "cleared", "blocked"] = "pending"

class BlogAgent(AgentBase):
    agent_id = "blog-agent"
    version = "2.0.0"
    input_schema = BlogDraftInput
    output_schema = BlogDraft

    async def run(self, input_dp: BlogDraftInput) -> BlogDraft:
        # 1. Research-DP laden
        research = await self.ctx.dp_client.resolve(input_dp.research_ref)
        # 2. Style-Skill laden (falls angegeben)
        style_guide = ""
        if input_dp.style_ref:
            skill = await self.ctx.skill_store.get(input_dp.style_ref)
            style_guide = skill.body if skill else ""
        # 3. Blog-Draft generieren (LLM via LiteLLM, nicht direkt)
        draft = await self._generate_draft(research, style_guide, input_dp.target_format)
        return BlogDraft(
            tenant_id=self.ctx.tenant_id,
            produced_by=self.agent_id,
            title=draft.title,
            body=draft.body,
            teaser=draft.teaser,
            word_count=len(draft.body.split()),
            research_ref=input_dp.research_ref,
        )
```

**Blog-Workflow (LangGraph):**

```python
# core/workflow-engine/workflows/blog_workflow.py
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt

class BlogWorkflowState(TypedDict):
    tenant_id: str
    intent_params: dict
    research_dp: dict | None
    draft_dp: dict | None
    compliance_dp: dict | None
    approved: bool

graph = StateGraph(BlogWorkflowState)

graph.add_node("research", research_node)        # → ResearchResult
graph.add_node("draft", draft_node)              # → BlogDraft
graph.add_node("compliance", compliance_node)    # → ComplianceReport
graph.add_node("human_review", human_review_node)  # interrupt() — wartet auf Mensch
graph.add_node("publish", publish_node)          # → BlogPublished

graph.add_edge("research", "draft")
graph.add_edge("draft", "compliance")
graph.add_conditional_edges("compliance", route_compliance,
    {"cleared": "human_review", "blocked": END})
graph.add_conditional_edges("human_review", route_approval,
    {"approved": "publish", "rejected": END})

def human_review_node(state: BlogWorkflowState):
    """Human-in-the-Loop: wartet auf Approval in Console."""
    interrupt({
        "message": "Blog-Draft bereit zur Review",
        "draft_dp_id": state["draft_dp"]["dp_id"],
        "tenant_id": state["tenant_id"],
    })
    return state  # Weiter nach interrupt() resume
```

### 9.3 Email-Agent

Port von `packages/email-agent/` — wichtigste Funktionen:
- Gmail-Integration via MCP (OAuth2-Scopes schützen — Bug aus v1 behoben)
- Rechnungs-Extraktion als DataProduct
- Steuer-Export als DataProduct

```python
class InvoiceExport(DataProduct):
    invoices: list[Invoice]
    tax_year: int
    total_amount: float
    export_format: Literal["csv", "json", "xlsx"] = "json"
    # Compliance: PII in Rechnungen wird vor Speicherung gecheckt
    pii_cleared: bool = False
```

### 9.4 Kommunikationsmanager-Agent (`comms-manager-agent`)

**SKU / Paket:** `agents/comms-manager/` · Compose: `deploy/agents/comms-manager.yml`  
**Rolle:** Fachlicher Agent für **Kontakte, Meeting-Teilnehmer und Kalender-Kontext** — nicht Orchestrator-Direct-HTTP.

> **Architekturregel (P5/P8):** Externe Welt und Brain-Lesen **nur** über `self.mcp`.  
> Brain-Schreiben **nur** als typisierte DataProducts → `POST /v1/dataproduct/commit` (vom Platform-Orchestrator, nicht frei upserten).  
> **Kein Workaround:** Die heutige Console-Bridge `POST /v1/meetings/participants/{process,commit}` ist **provisorisch** (Phase-2-Übergang) und wird durch Dispatch an diesen Agenten ersetzt, sobald Platform-Gate grün ist.

**Konsumiert (Input-DPs):**

| Input-DP | Quelle | Beispiel |
|----------|--------|----------|
| `comms:ParticipantListRaw` | Console Paste, Calendar-MCP, Mail-Header | Google-Kalender-Teilnehmer kopiert |
| `comms:MeetingContext` | Meeting-Inbox, time-agent | Titel, `held_at`, optionale Summary |
| optional `org:Meeting` | time-agent (Calendar-MCP) | Bestehendes Graph-Meeting verknüpfen |

**Liefert (Output-DPs → Commit):**

| Output-DP | storage_target | Kanten |
|-----------|----------------|--------|
| `OrgPerson` | G | — |
| `OrgOrganization` | G | aus Mail-Domain (kein Gmail/GMX) |
| `OrgMeeting` | G | `attended_by` → Person; `about` → Engagement |

**MCP-Tools (Allowlist, keine Direkt-Calls):**

| MCP | Cap | Zweck |
|-----|-----|-------|
| `calendar` | `list_attendees`, `get_event` | Teilnehmer aus Termin |
| `mail` | `parse_headers` | Absender/CC → Person |
| `web_search` | `search` | LinkedIn-Profil, Firmenwebsite (SearXNG) |
| `kg` | `search`, `resolve` | Bestehende Person/Org per E-Mail |
| `memory` | `ask` | optional Kontext „wer ist X?“ |

**Workflow (LangGraph, deterministische Hülle):**

```
1. Parse (Code, kein LLM)     → E-Mails + Namen aus Raw-Text (Google-Formate)
2. Resolve (MCP kg)           → bestehende org:Person per E-Mail
3. Enrich (MCP web_search)    → LinkedIn, Firmenwebseite — Vorschläge mit confidence
4. Merge (Code)               → Human-in-the-Loop: nicht blind überschreiben
5. Commit (Platform)          → OrgPerson, OrgOrganization, OrgMeeting DPs
6. Output                     → comms:ParticipantEnrichmentReport (Summary für Console)
```

```python
# agents/comms-manager/agent.py — Skizze (Phase 4, nach Gate)
class ParticipantListRaw(DataProduct):
    raw_text: str
    source: Literal["google_calendar_paste", "calendar_mcp", "mail_headers"]
    meeting_ref: str | None = None  # SQLite-Inbox-ID oder org:Meeting

class ParticipantEnrichmentReport(DataProduct):
    participants: list[dict]  # email, name, status, linkedin_url?, company_website?
    summary: str
    committed_refs: list[str]  # person_ids

class CommsManagerAgent(AgentBase):
    agent_id = "comms-manager-agent"
    input_schema = ParticipantListRaw
    output_schema = ParticipantEnrichmentReport

    async def run(self, input_dp: ParticipantListRaw) -> ParticipantEnrichmentReport:
        parsed = parse_participants(input_dp.raw_text)  # deterministisch (P4)
        for p in parsed:
            existing = await self.mcp.call("kg", "resolve_by_email", {"email": p.email})
            if input_dp.source != "google_calendar_paste":
                ...
            enrich = await self.mcp.call("web_search", "search",
                                         {"q": f'site:linkedin.com/in "{p.name}"'})
        # → OrgPerson / OrgOrganization / OrgMeeting DPs committen lassen (Platform)
        ...
```

**Console-Anbindung (Zielbild Phase 4+):**

- Meeting-Formular `/meetings`: Paste → `POST /v1/dispatch` mit Intent `participant_enrich` → comms-manager-agent  
- **Nicht:** Orchestrator-interne HTTP-Enrichment-Endpunkte als Dauerlösung  
- Übergang bis Gate: bestehende `/v1/meetings/participants/*` als dokumentierte Bridge ([docs/15-MEETINGS.md](docs/15-MEETINGS.md))

**Abnahme (zusätzlich zu Contract-Tests):**

```
GATE-COMMS-01  Agent nutzt ausschließlich self.mcp (kein httpx/duckduckgo im Orchestrator-Pfad)
GATE-COMMS-02  Output = ParticipantEnrichmentReport + OrgPerson-Commits in A auditierbar
GATE-COMMS-03  E2E: Google-Paste → Dispatch → Graph enthält Person + attended_by-Kante
GATE-COMMS-04  Bestehende Person per E-Mail wird gemerged, nicht blind überschrieben
```

**Verwandte Agenten:**

| Agent | Abgrenzung |
|-------|------------|
| **time-agent** | Calendar-MCP → `org:Meeting` (Termin-Metadaten, nicht Enrichment) |
| **email-agent** | Rechnungen, Steuer-Export — nicht Teilnehmer/Kontakte |
| **comms-manager** | Personen, Organisationen, Meeting-Teilnehmer, LinkedIn/Web-Anreicherung |

---

## 10. Phase 5 — Console vollständig

**Dauer:** 1 Woche  
**Ziel:** 3-Ebenen-IA vollständig, alle Kernrouten  
**Akzeptanzkriterium:** Alle Workflows aus Console steuerbar, kein Legacy-HTMX

### 10.1 3-Ebenen-Information-Architecture

**Designprinzip:** 80/15/5-Regel

- **80 % der Nutzung** → Ebene 1 (Lagebild) — maximal simpel, keine Infrastruktur-Details
- **15 % der Nutzung** → Ebene 2 (Workflows) — Task-Management, nicht Agent-Details
- **5 % der Nutzung** → Ebene 3 (Plattform) — Nur wenn etwas kaputt ist

```typescript
// src/app/page.tsx — Ebene 1: Lagebild
// Zeigt NUR:
// - Letztes Briefing (1-Satz-Zusammenfassung + Link)
// - Offene Human-in-the-Loop-Tasks (Zahl + Typ)
// - Aktive Workflows (Zahl, kein Detail)
// - Letzte 3 produzierte DPs (Titel + Zeit)
// - 1 Alert wenn vorhanden (nicht alle)

// NICHT zeigen:
// - Pipeline-Details
// - Agent-Logs
// - Rohdaten
// - Config-Dumps
// - MCP-Server-Liste
```

### 10.2 Routen-Map

```
/                           Lagebild
/workflows                  Alle Workflows + Status
/workflows/briefing         Daily Briefing (starten + History)
/workflows/research         Recherche starten
/workflows/blog             Blog-Workflow (mit Human-Review-Gate)
/workflows/email            E-Mail / Steuer-Export
/workflows/[id]             Generischer Workflow-Status
/platform                   Plattform-Übersicht (selten öffnen)
/platform/storage           Memory-Stacks + VM-Festplatte
/platform/agents            Agenten-Status + Config
/platform/mcp               MCP-Gateway + Server-Status
/platform/kg                Knowledge Graph Visualisierung
/platform/skills            Skill-Bibliothek
/platform/monitor           Services + FinOps + Logs
/platform/tenants           Tenant-Management
/platform/receipts          Run-Receipts + Audit-Chain-Verifikation (P17)
/context/[runId]            LLM-Kontext eines Lagebild-/Dispatch-Runs (Prompt + Retrieval)
```

### 10.3 One-Command-Demo-Modus (NEU v2 — Vorbild Olla Nest/ArcaQ)

Für Time-to-Value: ein Befehl startet die komplette Platform mit Seed-Daten und einem geführten Demo-Durchlauf.

```bash
make demo   # infra + monitoring + core + platform-agents + seed-tenant "demo"
            # → öffnet Console, spielt daily-briefing + research end-to-end durch
            # → zeigt LangFuse-Trace, Unified-Search-Treffer, Run-Receipt
```

Senkt die Einstiegshürde für neue Nutzer/Kunden auf einen Befehl und dient zugleich als Smoke-Test der gesamten Platform.

---

## 11. Phase 6 — Multi-Tenant & GraphRAG

**Dauer:** 1 Woche  
**Ziel:** Echte Runtime-Isolation **innerhalb einer VM**, GraphRAG im Context Bundle, MCP M2  

**Abgrenzung zu P19:** Multi-Tenant hier = mehrere Tenants/Namespaces **auf derselben Appliance** (z. B. Demo-Sandbox neben `nextchapter` auf NCE-DEV).  
Kunden-PROD bleibt **eigene VM + eigenes Brain** — Phase 6 ersetzt diese physische Grenze nicht (§19 Isolationsmodell).

### 11.1 Multi-Tenant Runtime-Isolation

```python
# core/orchestrator/tenant_context.py
class TenantContext:
    tenant_id: str
    qdrant_namespace: str          # = f"tenant_{tenant_id}"
    letta_project_id: str
    kg_partition: str              # = tenant_id
    litellm_budget_id: str
    guardrails_policy: GuardrailsPolicy
    active_packages: list[str]     # Welche SKUs sind installiert?

    @classmethod
    def for_tenant(cls, tenant_id: str) -> "TenantContext":
        config = load_tenant_config(tenant_id)
        return cls(
            tenant_id=tenant_id,
            qdrant_namespace=f"tenant_{tenant_id}",
            letta_project_id=config.letta_project_id,
            kg_partition=tenant_id,
            litellm_budget_id=config.budget_id,
            guardrails_policy=load_policy(tenant_id),
            active_packages=config.packages,
        )
```

**Qdrant-Namespace-Isolation:**

```python
# Jeder Qdrant-Call trägt tenant_id als Filter
def qdrant_search(query: str, tenant_id: str, k: int = 5):
    return qdrant_client.search(
        collection_name="content",
        query_vector=embed(query),
        query_filter=Filter(
            must=[FieldCondition(key="tenant_id",
                                  match=MatchValue(value=tenant_id))]
        ),
        limit=k,
    )
```

### 11.2 GraphRAG

RetrievalSlice im Context Bundle kombiniert Vektor + Graph.  
**Voraussetzung:** Company-Brain-Gate (§12.4.5) bestanden — sonst kein GraphRAG als Produktfeature.

```python
# core/orchestrator/context_resolution.py — Erweiterung
def build_retrieval_slice(intent: str, tenant_id: str) -> RetrievalSlice:
    # 1. Vektor-Suche (L1) — nur kuratiert (P2)
    vector_chunks = qdrant_search(intent, tenant_id, k=5)

    # 2. Entitäten aus Query extrahieren (Regel/NER — kein freies LLM-Routing)
    entities = extract_entities(intent)

    # 3. Graph-Traversal über MCP kg.traverse (P5) — hops=2, org:* priorisiert
    graph_context = []
    for entity in entities:
        nodes = kg_traverse(
            entity, tenant_id, hops=2,
            type_filter=["org:*", "blog:*", "platform:*", "email:*"],
        )
        graph_context.extend(nodes)

    # 4. Kombinierter Kontext (Score-Fusion Platform — P11)
    return RetrievalSlice(
        chunks=vector_chunks,
        graph_nodes=graph_context,
        combined=merge_vector_and_graph(vector_chunks, graph_context),
    )
```

### 11.3 MCP M2 — Externe Server als Sidecars

```yaml
# deploy/core.yml — MCP-Sidecar-Services
services:
  mcp-github:
    image: ghcr.io/github/github-mcp-server:latest
    environment:
      GITHUB_TOKEN: ${GITHUB_TOKEN}

  mcp-calendar:
    image: ghcr.io/modelcontextprotocol/google-calendar:latest
    environment:
      GOOGLE_CREDENTIALS: ${GOOGLE_CREDENTIALS_JSON}
```

```yaml
# config/mcp-servers.yaml — Externe Server
servers:
  github:
    type: external
    host: mcp-github
    port: 3000
    protocol: stdio
    allowed_tenants: [nextchapter]
    caps:
      max_calls_per_hour: 100

  calendar:
    type: external
    host: mcp-calendar
    port: 3001
    allowed_tenants: [nextchapter]
```

---

## 12. Datenschicht im Detail

### 12.1 Sechs Schichten — Regeln

| Schicht | Speicher | Was darf rein | Wer schreibt | Retention |
|---------|----------|---------------|--------------|-----------|
| **L0** | YAML-Files | Entity/Edge-Type-Definitionen | Entwickler | Permanent |
| **K** | Dateisystem | Kuratierte Dokumente, Wissensbaum | Ingest-Agent, Publish | Permanent |
| **G** | Postgres (kg_nodes, kg_edges) | Entitäten, Beziehungen, DP-Commits | DP-Service, Curators | Permanent, versioniert |
| **L1** | Qdrant | Embeddings kuratierter/published Inhalte | Ingest-Agent, L1-Curator | 90 Tage rolling |
| **L2** | Letta Archival | Episodische Zusammenfassungen | L2-Curator | Permanent |
| **L3** | Letta Core | Fakten, User-Modell | L3-Curator | Permanent |
| **SK** | SQLite + Qdrant | Skill-Dokumente | Skill-Distiller | Permanent, versioniert |
| **A** | Postgres (ai_os_log) | AgentRun-Records, MCP-Calls | Orchestrator, MCP-Gateway | Permanent, unveränderlich |

**Verboten:** LLM entscheidet über Speicherziel — immer deterministischer Code.

### 12.2 Knowledge Graph — Schema

```yaml
# config/kg-platform-schema.yaml
entities:
  - type: platform:Tenant
    fields: [id, name, created_at, active_packages]

  - type: platform:AgentRun
    fields: [id, intent, tenant_id, agent_id, status, started_at, ended_at]

  - type: platform:DataProduct
    fields: [id, type, tenant_id, produced_by, produced_at, storage_targets]

  - type: platform:Skill
    fields: [id, title, tenant_id, version, success_rate, use_count]

  - type: blog:BlogDraft
    fields: [id, title, word_count, compliance_status, tenant_id]

  - type: blog:BlogPublished
    fields: [id, title, url, published_at, tenant_id]

  - type: research:ResearchSession
    fields: [id, query, confidence, source_count, tenant_id]

  - type: email:Invoice
    fields: [id, supplier, amount, date, tenant_id]

  # Company Brain (P18) — vollständige Spec: docs/09-COMPANY-BRAIN.md
  - type: org:Person
  - type: org:Organization
  - type: org:Offering
  - type: org:Engagement
  - type: org:Meeting
  - type: org:Decision
  - type: org:Policy
  - type: org:KnowledgeAsset
  - type: org:Claim
  # org:Skill → alias platform:Skill

edges:
  - type: PRODUCED_BY      # DataProduct → AgentRun
  - type: PART_OF          # DataProduct → Workflow
  - type: DERIVED_FROM     # DataProduct → DataProduct (Input)
  - type: BELONGS_TO       # alle → Tenant
  - type: PUBLISHED_TO     # BlogDraft → BlogPublished
  - type: COMPLIANCE_CLEARED  # BlogDraft → ComplianceReport
  - type: SUPERSEDES       # Skill v2 → Skill v1 · Decision/Policy
  - type: AUTHORED_BY      # Document → Person
  - type: ATTENDED_BY      # Meeting → Person
  - type: ABOUT            # Meeting|Decision → Offering|Engagement|Organization
  - type: DECIDED_IN       # Decision → Meeting
  - type: APPLIES_TO       # Policy → Offering|Engagement
  - type: DOCUMENTS        # KnowledgeAsset → Decision|Meeting|Offering|Policy
  - type: ASSERTS          # KnowledgeAsset|AgentRun → Claim
  - type: SUPPORTS         # Claim → BlogPublished|Offering|Engagement|Decision
```

L0-Dateien: `config/kg-platform-schema.yaml` (Kern) + `packages/org-brain/schema/{entities,edges}.yaml` (Company Brain).

### 12.3 Memory-Flywheel

```
Jede Aktion:
  → DP-Commit → G (KG) + K (files) + ggf. L1

Täglich (L2-Curator):
  L1-Chunks der letzten 24h → LLM-Verdichtung → Letta Archival Memory (L2)
  (= episodisch, NICHT Company-Brain-SSOT)

Wöchentlich (L3-Curator):
  Letta Archival (7 Tage) → LLM-Fakten-Extraktion
  → nur stabile Fakten als OrgClaim DataProduct
  → DP-Commit → G (org:Claim + asserts/supports)
  → KEINE Direkt-Writes Letta→Postgres ohne DP-Pfad (P8/P9)

Nach jedem komplexen Task (Skill-Distiller):
  AgentRun → LLM-Skill-Destillation → Skill-Store (Markdown + Index)

Ergebnis: Jede Nutzung macht das System klüger — Firmenwahrheit wächst in G/K,
Agent-Episoden in Letta, Verfahren in SK.
```

### 12.4 Company Brain — Wissensmanagement

**Vollständige Spezifikation:** [docs/09-COMPANY-BRAIN.md](docs/09-COMPANY-BRAIN.md)  
**Prinzip:** P18 · **Impuls:** Company Brain (SSOT) statt persönlicher Second Brains.  
**Isolation (P19):** Brain **pro Platform-VM**. NCE First-Party auf DEV-Werkstatt-VM; jeder Kunde = eigene PROD-VM + eigene Volumes. Keine gemeinsame DB, kein Auto-Sync. → [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md) § Isolationsmodell.

#### 12.4.1 Rolle im Stack (kein Architekturbruch)

| Schicht | Rolle im Company Brain |
|---------|------------------------|
| **K** | Kanonische Wahrheit (Dateien, Seed, Decisions als MD) |
| **G** | Abfragbare Beziehungen (`org:*` + Fach-SKU-Typen) |
| **L1** | Nur kuratierte/published Chunks — nie Roh-Chat |
| **L2/L3 Letta** | Agent-Runtime / Destillationsquelle — **nicht** SSOT |
| **SK** | Verdichtete Verfahren |
| **A** | Wer hat wann welchen Brain-Write ausgelöst |

**Kommunikations- und Schreibregeln (unverändert P5/P8/P9):**

1. Fach-Agenten kommunizieren **nur** über `self.mcp` (kein Direct-HTTP, kein Direct-SQL auf `kg_*`).
2. Fach-Agenten **konsumieren** Brain-Wissen über MCP `kg.search|traverse|resolve` und/oder Platform `POST /v1/search`.
3. Fach-Agenten **liefern** Brain-Änderungen ausschließlich als typisierte **DataProducts**; Persistenz nur über `POST /v1/dataproduct/commit`.
4. MCP `kg.upsert_node|upsert_edge` ist Caps-mäßig auf Platform-Rollen beschränkt (DP-Service, memory-agent) — siehe §13.1.
5. Human-Gate für `OrgDecision` mit Statuswechsel nach `active` (Console Ebene 2 / Interrupt in LangGraph).

#### 12.4.2 Mindest-Ontologie `org:*` (10 Entities / 8 Edges)

Siehe [09-COMPANY-BRAIN.md §3](docs/09-COMPANY-BRAIN.md#3-l0-schema--mindest-ontologie-org). Kurz:

- Entities: Person, Organization, Offering, Engagement, Meeting, Decision, Policy, KnowledgeAsset, Claim, Skill(=platform:Skill)
- Edges: attended_by, about, decided_in, supersedes, applies_to, documents, asserts, supports

Blog (`blog:*`) und Email (`email:*`) bleiben eigene SKUs — Company Brain **verbindet** sie (z. B. Claim `supports` BlogPublished), ersetzt sie nicht.

#### 12.4.3 Datenprodukte (Storage-Targets fix im Schema)

| DP | storage_target | Wer produziert |
|----|----------------|----------------|
| OrgOffering, OrgPolicy, OrgEngagement | G+K | Seed / Console |
| OrgMeeting | G | time-agent (Calendar-MCP → DP) |
| OrgDecision | G+K | Console oder Workflow + Human-Gate |
| OrgKnowledgeAsset | G+K (+L1 wenn published) | ingest-agent |
| OrgClaim | G | memory-agent L3-Curator (`confidence≥0.7` Default-Retrieval) |
| OrgPerson, OrgOrganization | G | Seed / **comms-manager-agent** (nicht Orchestrator-Direct) |

#### 12.4.4 Ingest-Quellen → Schichten (Next Chapter)

| Quelle | Ziel | KG |
|--------|------|-----|
| Content Factory Publish | K+L1 | bestehende `blog:*` |
| Gmail Invoices | G (+ Sheet) | bestehende `email:*` |
| Calendar MCP | G | `org:Meeting` (time-agent) |
| Google-Teilnehmer / Kontakt-Anreicherung | G | **comms-manager-agent** (MCP web_search + kg) |
| Meeting-Notizen / Transkript → Inbox | K→Ingest | Meeting + optional Decision (Gate) |
| `knowledge/` + Portfolio | K | Offering, Policy, KnowledgeAsset |
| Chat-Import | L2; Claims nur via L3-Curator | `org:Claim` sparsam |
| Skill-Distiller | SK | platform:Skill |

#### 12.4.5 Company-Brain-Gate (Zusatz zum Platform-Gate)

Vor dem Label „Company Brain“ in Produkt/Console:

```
GATE-CB-01  packages/org-brain/schema/* geladen in Schema-Registry
GATE-CB-02  Tenant nextchapter: ≥10 org:* Nodes + ≥5 fachliche Edges
GATE-CB-03  Abnahmefragen 1–5 (09-COMPANY-BRAIN §8) per API ohne reine Vektor-Rate
GATE-CB-04  Kein Fach-Agent mit Direct-Write auf kg_* (Contract-Test)
GATE-CB-05  L3-Curator schreibt Claims nur über DP-Commit (Integrationstest)
GATE-CB-06  Query-Router: Decision-Intent ohne L1/Letta im Plan (Contract-Test)
GATE-CB-07  Claim-Dedup + supports→Offering/Decision braucht Human-Gate
GATE-CB-08  Atomarer Commit G+K: kein active Decision-Node ohne K-Datei
```

#### 12.4.6 Phasen-Einbettung

| Phase | Company-Brain-Arbeit |
|-------|----------------------|
| 0 | L0 YAML `org-brain` im Repo |
| 1 | Search-Index-Hook kennt `org:*` · **Query-Router** (§12.4.7) |
| 2 | DP-Klassen, **atomarer G+K-Commit**, Claim-Pipeline, MCP Caps, Seed, GATE-CB-* |
| 4 | time-agent→Meeting; **comms-manager**→Person/Org; blog↔supports/cites |
| 5 | Console KG-Filter `org:*`, Decision-Inbox, Claim-Gate-UI |
| 6 | GraphRAG DomainSlice/RetrievalSlice priorisiert `org:*` (nur mit Router) |

#### 12.4.7 Betriebsoptimierungen (verbindlich)

Vollständige Spec: [docs/09-COMPANY-BRAIN.md §12](docs/09-COMPANY-BRAIN.md#12-betriebsoptimierungen-verbindlich).

| # | Maßnahme | Kernregel | Phase |
|---|----------|-----------|-------|
| **1** | **Query-Router** | Deterministisch (P4): Intent → welche Schichten. Decision/Policy → nur G(+K); Episode → nur Letta; Ähnlichkeit → L1. Nie alle Schichten blind. | 1 |
| **2** | **Claim-Pipeline härten** | confidence≥0.7 · Dedup Cosine≥0.95 · Provenance Pflicht · `supports`→Offering/Decision = Human-Gate · Cap 50/Lauf | 2 |
| **3** | **Atomarer Commit K↔G** | Typen mit storage_target G+K: Datei + Node + Edges + Audit in einer Unit-of-Work; Rollback bei Fehler | 2 |

```python
# Einordnung im Hot Path (Phase 1+)
intent → query_router.plan(intent) → nur geplante Slices befüllen
       → Unified Search / DomainSlice / RetrievalSlice / EpisodicSlice
```

**Verboten:** Default-Plan mit `use_l1=True` und `use_letta=True` gleichzeitig für Geltungsfragen.

---

## 13. MCP-Gateway im Detail

### 13.1 Native Adapter M1 (aus v1 portieren)

Alle Adapter aus `stack/scripts/tools/mcp_adapters.py` portieren:

| Adapter | Tool-Names | Aus v1 |
|---------|-----------|--------|
| `web_search` | `search` | ✅ portieren |
| `qdrant_search` | `search`, `upsert` | ✅ portieren |
| `mail` | `get_recent`, `send`, `get_by_id` | ✅ portieren |
| `calendar` | `get_today`, `get_week`, `create_event` | ✅ portieren |
| `cms_git` | `get_draft`, `publish`, `list_drafts` | ✅ portieren |
| `memory` | `add_archival`, `search_archival` | ✅ portieren |
| `console` | `push_notification` | NEU |
| `kg` | `search`, `traverse`, `resolve`, `upsert_node`, `upsert_edge` | ✅ portieren + erweitern (P18) |

**MCP `kg` Caps (P18 / Company Brain):**

| Tool | `allowed_callers` | Cap |
|------|-------------------|-----|
| `search`, `traverse`, `resolve` | alle Agenten (Tenant-Filter Pflicht) | hops≤2, max 20 nodes/call |
| `upsert_node`, `upsert_edge` | nur `dp-service`, `memory-agent` | max 50/h/tenant |

Fach-Agenten schreiben Graph **nicht** per upsert — nur via Output-DataProduct → Commit (§12.4.1).

### 13.2 Caps + Audit

```python
# config/mcp-servers.yaml
servers:
  web_search:
    type: native
    adapter: web_search
    caps:
      max_calls_per_workflow: 10
      max_calls_per_hour_per_tenant: 100
    audit: true
    allowed_tenants: all
```

---

## 14. Skill-Loop im Detail

### 14.1 Skill-Dokument-Format

```markdown
---
id: blog-research-to-draft
title: Blog-Artikel aus Research-Brief erstellen
version: 3
created: 2026-07-01
last_refined: 2026-07-10
tenant_id: nextchapter
produced_by: blog-agent
success_rate: 0.89
use_count: 12
use_when:
  - Ein Research-Brief liegt vor und ein Blog-Artikel soll erstellt werden
  - Format "linkedin" oder "blog" gewünscht
tags: [blog, content, writing]
---

## Ablauf

1. Research-DP über dp_client.resolve() laden (nicht neu recherchieren)
2. Style-Guide für Tenant aus Skill-Store laden (falls vorhanden: `nextchapter-brand-voice`)
3. Zielformat prüfen: linkedin = max 300 Wörter + Hook, blog = 800–1200 Wörter + SEO-Title
4. Draft in einem LLM-Call generieren (kein iterativer Schleife — erhöht Kosten)
5. Compliance-Status immer auf "pending" setzen — niemals "cleared" im Agent

## Bekannte Fallstricke

- Research-Brief ohne Quellen → Confidence fällt unter 0.6 → Hinweis an Nutzer
- LinkedIn-Format: immer ohne H2/H3-Überschriften, nur Emojis als Gliederung
- Tenant nextchapter: "Wir"-Form vermeiden, immer "Peter"/"NCE"

## Verbesserungen (Version 3)

- v1: Kein Style-Guide geladen → Stil-Inkonsistenz
- v2: Style-Guide geladen, aber Format-Check fehlte
- v3: Format-Check vor Generierung → weniger Nacharbeit
```

### 14.2 Skill-Verfeinerung (Refinement)

```python
# core/skill-service/skill_refiner.py
class SkillRefiner:
    async def refine(self, skill: Skill, new_run: AgentRun) -> Skill:
        """Nach Wiederholung: Skill verbessern, nicht ersetzen."""
        prompt = f"""
Bestehender Skill (Version {skill.version}):
{skill.body}

Neuer Lauf:
- Ergebnis: {new_run.outcome}
- Besonderheiten: {new_run.notes}
- Abweichungen vom Skill: {diff(skill.steps, new_run.actual_steps)}

Aktualisiere den Skill:
- Behalte was funktioniert hat
- Ergänze neue Erkenntnisse unter "Bekannte Fallstricke"
- Aktualisiere "Ablauf" wenn ein Schritt verbessert wurde
- Füge "Verbesserungen (Version {skill.version+1})" hinzu
"""
        updated_body = await llm.complete(prompt)
        return Skill(
            id=skill.id,
            title=skill.title,
            version=skill.version + 1,
            body=updated_body,
            success_rate=self._update_success_rate(skill, new_run),
            use_count=skill.use_count + 1,
        )
```

---

## 15. Tenant-Modell im Detail

### 15.1 Tenant-Konfiguration

```yaml
# customers/nextchapter/context-system.yaml
tenant_id: nextchapter
name: NextChapter Experts

packages:
  - research-agent
  - blog-agent
  - email-agent

compute_mode: balanced   # sovereign | balanced | premium

knowledge:
  brand_voice: knowledge/brand-voice.md
  style_guides: knowledge/style-guides/
  compliance_rules: compliance/rules.yaml

context_bootstrap:
  entities:
    - type: platform:Tenant
      id: nextchapter
      name: NextChapter Experts
  seed_knowledge:
    - knowledge/about-nce.md
    - knowledge/target-audience.md

routing:
  # Intent → Workflow-Name
  blog: blog-workflow
  research: research-workflow
  email: email-workflow
  briefing: daily-briefing

litellm_budget:
  monthly_usd: 50
  alert_at_pct: 80
```

### 15.2 Tenant-Bootstrap

```python
# Beim ersten Deploy eines Tenants
async def bootstrap_tenant(tenant_id: str):
    config = load_tenant_config(tenant_id)

    # 1. Qdrant-Namespace erstellen
    await qdrant.create_namespace(f"tenant_{tenant_id}")

    # 2. Letta-Projekt erstellen
    letta_project_id = await letta.create_project(tenant_id)

    # 3. KG-Partition: Root-Knoten
    await kg.upsert_node({
        "type": "platform:Tenant",
        "id": tenant_id,
        "name": config.name,
    }, tenant_id=tenant_id)

    # 4. Seed-Knowledge indexieren
    for path in config.context_bootstrap.seed_knowledge:
        await ingest_agent.ingest_file(path, tenant_id)

    # 5. LiteLLM-Budget einrichten
    await litellm.create_budget(tenant_id, config.litellm_budget)
```

---

## 16. Test-Strategie

### 16.1 Test-Pyramide

```
                    ┌─────────────────┐
                    │  E2E-Tests      │  5 Tests
                    │  (Docker-Stack) │
                ┌───┴─────────────────┴───┐
                │  Integrations-Tests      │  20 Tests
                │  (Services + DB)         │
           ┌────┴──────────────────────────┴────┐
           │  Unit-Tests                         │  50+ Tests
           │  (Einzel-Module, Mock-Dependencies) │
      ┌────┴────────────────────────────────────┴────┐
      │  Contract-Tests (SDK)                         │  10 Tests
      │  Jeder Agent muss bestehen                    │
      └───────────────────────────────────────────────┘
```

### 16.2 Test-IDs (aus v1 portieren + erweitern)

| ID | Typ | Prüfung |
|----|-----|---------|
| CONTRACT-01 | Unit | Agent ohne agent_id schlägt fehl |
| CONTRACT-02 | Unit | Agent ohne output_schema schlägt fehl |
| CONTRACT-03 | Unit | execute() committed immer ein DP |
| DP-01 | Unit | Schema-Registry validate_node_type |
| DP-02 | Integration | POST /v1/dataproduct/commit → KG-Eintrag |
| CTX-01 | Unit | resolve_context gibt 6 Slices zurück |
| CTX-02 | Integration | Tenant-Isolation: Tenant A sieht Tenant B nicht |
| MCP-01 | Integration | web_search call via MCP-Gateway |
| MCP-02 | Integration | Caps: Überschreitung → 429 |
| MCP-03 | Integration | Audit: jeder MCP-Call in ai_os_log |
| WF-01 | Integration | daily-briefing Workflow läuft durch |
| WF-02 | Integration | blog-workflow mit interrupt() |
| WF-03 | Integration | Checkpoint: Workflow nach Neustart fortsetzbar |
| SKILL-01 | Unit | Skill-Distiller produziert valides Markdown |
| SKILL-02 | Integration | Skill-Store: save + find_relevant |
| SKILL-03 | Integration | Skill-Refinement erhöht Version |
| SCHED-01 | Integration | Cron-Job läuft zum geplanten Zeitpunkt |
| GQ-01 | E2E | Forschungsanfrage: Antwort in < 15s |
| GQ-02 | E2E | Blog-Workflow E2E inkl. Human-Review |

### 16.3 Golden-Query-Tests (aus v1 portieren)

```bash
python tests/golden/golden_runner.py --tenant nextchapter --query "research" \
  --expected-contains "Zusammenfassung" --max-latency 15
```

### 16.4 Lokales Modell — Capability-Tests (Ollama)

Praxis-Tests gegen das LAN-Modell (Use Cases: E-Mail-JSON, Kalender, Routing, Tool-Calling, Übersetzung, Datenprodukte, Recherche mit/ohne SearXNG).

| ID | Typ | Prüfung |
|----|-----|---------|
| QWEN-01 | Capability | E-Mail-Suchfilter als JSON |
| QWEN-02 | Capability | Kalender-Tages-Briefing |
| QWEN-03 | Capability | Workflow-Routing (Intent + Steps) |
| QWEN-04 | Capability | Tool-Calling (Kalender + E-Mail) |
| QWEN-05 | Capability | Übersetzung DE→EN |
| QWEN-06 | Capability | Strukturiertes Datenprodukt `email:MailSummary` |
| QWEN-07 | Capability | Recherche ohne Web-Kontext (Negativtest) |
| QWEN-08 | Capability | Recherche mit SearXNG-Kontext |

**Protokolle:** [docs/07-LOKALES-MODELL-TESTPROTOKOLL.md](docs/07-LOKALES-MODELL-TESTPROTOKOLL.md)

**Memory-Regression (Orchestrator):** `testcases/memory/cases/*.yaml` — 70+ Cases gegen `/v1/dispatch`, `/v1/search`, Storage-API. Runner: `./scripts/run-memory-testcases.py [--category episodic|working|storage]`.

**Compute-Regression:** `testcases/compute/cases/*.yaml` — Modus-API, LiteLLM-Inference, Intent-Routing (`Was steht heute an` → `daily_open_loops`). Runner: `python3 scripts/run-compute-mode-testcases.py`. **Letzter Lauf:** 2026-07-26 — **14/14 PASS**.

**Letzter Lauf:** 2026-07-12 — `qwen3.6-64k:latest` @ `192.168.178.64:11434` → **6/8 PASS** (QWEN-04 Skript-Bug, QWEN-07 erwartetes Halluzinationsrisiko)

```bash
python3 ../1000-AI-OS/stack/scripts/tools/test_qwen_capabilities.py
```

---

## 17. Was aus v1 übernommen wird

### Direkt portieren (minimale Änderungen)

| v1-Pfad | v2-Pfad | Änderung |
|---------|---------|---------|
| `stack/scripts/tools/context_resolution.py` | `core/orchestrator/context_resolution.py` | SkillSlice hinzufügen |
| `stack/scripts/tools/dataproduct.py` | `sdk/dataproduct.py` | Pydantic v2 |
| `stack/scripts/tools/schema_registry.py` | `sdk/schema_registry.py` | Keine |
| `stack/scripts/tools/mcp_adapters.py` | `core/mcp-gateway/adapters/*.py` | Aufteilen |
| `stack/scripts/tools/knowledge_graph.py` | `core/orchestrator/kg_client.py` | Keine |
| `stack/scripts/tools/embed.py` | `sdk/embed.py` | Keine |
| `stack/scripts/tools/l1_curator.py` | `core/memory/l1_curator.py` | Keine |
| `stack/scripts/tools/guardrails.py` | `platform-agents/guardrails-agent/` | + L3 PII |
| `stack/config/` | `config/` | Bereinigen |
| `customers/` | `customers/` | Keine |
| `stack/tests/golden/` | `tests/golden/` | Keine |
| `stack/console-web/src/lib/` | `core/console/src/lib/` | Routen anpassen |

### Als Referenz behalten, in v2 neu implementieren

| v1-Konzept | v2-Implementierung |
|-----------|-------------------|
| `workflow_runner.py` | LangGraph-basierte Engine |
| `platform_runtime.py` | Generischer Dispatch mit Contract-Check |
| `pipeline.py` | PipelineAgent(AgentBase) |
| Console-Routen | Neue 3-Ebenen-IA |
| `packages/research-agent/` | `agents/research/` mit SDK-Contract |

---

## 18. Bekannte Fallstricke aus v1

Aus v1 gelernte Probleme die v2 vermeiden muss:

1. **OAuth-Scopes nicht schützen** (Bug v1: `ce07801`)  
   → v2: `mcp_adapter.py` validiert OAuth-Scope vor jedem Call, nicht im Agenten

2. **Ollama-Embedding-Fallback nicht konfiguriert** (Bug v1: `67aa7f4`)  
   → v2: `embed.py` hat expliziten Fallback-Chain: lokal → OpenAI → error

3. **Agenten die MCP umgehen** (v1: direkte HTTP-Calls in einigen Scripts)  
   → v2: Contract-Validator prüft zur Laufzeit ob HTTP-Calls außerhalb von MCPAdapter existieren

4. **Legacy-Console überlebt zu lange** (v1: HTMX-Console :8094 läuft noch)  
   → v2: Kein Legacy — Day 1 nur Next.js

5. **Zu viele Details in der Haupt-UI** (v1: alle Routen gleich prominent)  
   → v2: Strikte 3-Ebenen-IA, Ebene-3 hinter /platform

6. **Datenprodukte werden umgangen** (v1: Agenten schreiben direkt in Postgres/Qdrant)  
   → v2: AgentBase.execute() committed immer — kein direkter DB-Zugriff aus Agenten

7. **Scheduler nie gebaut, weil „bald"** (v1: P2-Blocker seit Monaten)  
   → v2: Scheduler ist Phase 2, nicht Phase 7

8. **Workflow-Runner eigener Code** (v1: functional aber nicht production-grade)  
   → v2: LangGraph von Anfang an

---

## 19. Deployment & Skalierung

### Leitprinzip

> **Ein Stack, alle Umgebungen.** Dev, Kunde, Enterprise nutzen dieselbe Architektur und dieselben Compose-Files. Unterschiede sind nur Hardware-Größe und aktive SKU-Pakete — kein Technologie-Tausch.  
> **Getrennte Welten:** Jede ausgelieferte VM hat **eigenes** Company Brain (Volumes/DB). Gleicher Stack ≠ geteilte Daten.

**Erstes Lizenzprodukt:** Platform-VM + `AIOS-CORE` — [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md) · Lizenz-Tiers: [docs/06-PRODUKT-DEPLOYMENT.md](docs/06-PRODUKT-DEPLOYMENT.md)

### Isolationsmodell (verbindlich — P19)

| Welt | VM | Company Brain | Wer schreibt |
|------|-----|---------------|--------------|
| **NCE Werkstatt** | DEV: Ubuntu Desktop + Cursor/Antigravity | **NCE** (`nextchapter` / NCE-Org) — First-Party | Dev-Tools + Console + Capture |
| **Kunde** | PROD: Ubuntu Server, Browser only | **nur dieser Kunde** | Kunden-Nutzung + seine Captures |

```text
[Tuxedo KVM-Host]
   └── DEV-VM  → Docker Stack + Volumes_A  → Brain NCE
[Hetzner/On-Prem]
   └── PROD-VM Kunde X → Docker Stack + Volumes_X → Brain X
   └── PROD-VM Kunde Y → Docker Stack + Volumes_Y → Brain Y
```

- Kein Auto-Sync DEV → PROD (nur bewusste Seeds/SKU-Doku).  
- Multi-Tenant **innerhalb** einer VM (Phase 6) ersetzt **nicht** diese VM-Grenze.  
- Optional: zweite NCE-VM ohne Cursor für eigenen „PROD-like“-Betrieb.

### Referenz-Architektur (fest)

```
Ubuntu 26.04 LTS · KVM-VM · Docker Compose
├── deploy/infra.yml + monitoring.yml     # immer
├── deploy/core.yml                       # Orchestrator, Search, Memory Gateway, Console
├── deploy/chat-capture.yml               # Phase 1b: Gemini/Antigravity → Gedächtnis
├── deploy/platform-agents.yml            # Pipeline, Ingest, Memory, Guardrails, Scheduler
└── deploy/agents/*.yml                   # Fach-Agenten (nach Platform-Gate)
```

### Skalierungsstufen (gleicher Stack, andere Größe)

| Stufe | Hardware | Inference | Zielgruppe / Brain |
|-------|----------|-----------|-------------------|
| **Dev** | KVM-VM auf Tuxedo, 16 GB RAM | Ollama remote (Hetzner GPU) | NCE Werkstatt — **Brain NCE** |
| **Starter** | Hetzner CX32 (€28/Mo) | Ollama remote + OpenRouter balanced | Erster Kunde — **Brain Kunde** (eigene VM) |
| **Pro** | Hetzner GEX44 (€184/Mo) | Ollama lokal (RTX 4000) | Souveränität + Performance |
| **Enterprise** | On-Premise Bare Metal | Ollama lokal, Air-Gap | Behörden, Finanz, Gesundheit |

**Betriebssystem:** Ubuntu 26.04 LTS „Resolute Raccoon" — Dev: Desktop, Produktion: Server (headless). LTS bis 2031.

### Developer-VM

```
[Tuxedo Laptop — KVM-Host]
    │
    └── KVM-VM: Ubuntu 26.04 Desktop
          ├── Cursor IDE (Electron, XWayland)
          ├── Antigravity
          ├── Git / Python / Node.js
          └── AI-OS v2 Stack (Docker Compose)
                ├── postgres, qdrant, letta
                ├── mcp-gateway, workflow-engine
                └── console-web :8092

[Hetzner Server — Remote]
    └── Ollama API :11434
          └── llama3.3, qwen2.5-coder, mistral...
          └── kein GPU in der lokalen VM nötig
```

```env
# .env in der Dev-VM
OLLAMA_HOST=http://hetzner-ip:11434   # Modell läuft remote, kein GPU-Passthrough nötig
```

**Antigravity / Cursor → AI-OS (kein Sync-Problem):**

```
Antigravity / Cursor → /opt/ai-os/ingest/inbox/*.md  (oder Capture-Pfad)
Ingest-Agent + Chat Capture (Docker, selbe VM) → L1/L2 (+ Audit)
Console / Unified Search → Wissen auffindbar
```

**Gemini / ChatGPT (Browser):** Chat Capture → `/v1/chat-import` → **NCE-Brain auf dieser DEV-VM**.  
Cursor, Antigravity, AI-OS, Git — eine DEV-VM, ein Dateisystem, **ein** Company Brain (NCE First-Party).

### Kunden-Deployment

```
[Kunden-VM / Hetzner Server]          ← physisch getrennt von NCE-DEV
    └── Ubuntu 26.04 Server (headless)
          └── AI-OS v2 (Docker Compose)
                ├── eigene Volumes (Brain Kunde)
                ├── Caddy (HTTPS, auto TLS)
                └── Console-Web → https://abc.ai-os.app

Kein Cursor, kein Antigravity. Nur Browser.
Kein Zugriff auf NCE-Volumes / NCE-Brain.
```

### Bootstrap Dev-VM (Ubuntu 26.04 Desktop)

```bash
# Auf dem Tuxedo Host: virt-manager installieren
sudo apt install virt-manager qemu-kvm libvirt-daemon-system

# VM anlegen: 16 GB RAM, 8 vCPUs, 150 GB qcow2
# ISO: ubuntu-26.04-desktop-amd64.iso (minimale Desktop-Installation)

# In der VM nach erstem Start:
sudo apt update && sudo apt upgrade -y

# Docker CE
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Cursor (AppImage, läuft via XWayland)
# → cursor-linux-x64.AppImage von cursor.sh herunterladen
chmod +x cursor-*.AppImage && ./cursor-*.AppImage --appimage-install

# AI-OS v2
git clone https://github.com/ncede/ai-os-v2.git /opt/ai-os
cd /opt/ai-os && cp .env.example .env
# OLLAMA_HOST=http://hetzner-ip:11434 setzen
docker compose up -d
```

### Bootstrap Kunden-VM (Ubuntu 26.04 Server)

```bash
# Hetzner: neuen Server mit Ubuntu 26.04 image anlegen, SSH rein:
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sh
sudo usermod -aG ubuntu docker

# aios-Installer (Lizenz-basiert, §06-PRODUKT-DEPLOYMENT)
curl -fsSL https://install.ai-os.app | bash -s -- --license=KUNDE-LICENSE-KEY
# prüft Lizenz, installiert Core, konfiguriert Caddy + HTTPS
# → https://abc.ai-os.app sofort erreichbar
```

### Container-Runtime: KVM

AI-OS v2 läuft in **KVM-VMs** auf Ubuntu 26.04 — Cursor, Docker und Ollama-Remote in einem Dateisystem, VM-Image portierbar via qcow2/Hetzner-Snapshot.

---

## 20. Monitoring: LangFuse

LangFuse startet in Phase 0 mit der Infra und ist ab Phase 1 in jedem LLM-Call und Workflow-Run aktiv. Zusammen mit dem Monitor-Agent (Platform, Phase 2) bildet LangFuse die Observability-Schicht.

### Deployment

```bash
# Immer mit Infra starten — nicht erst bei Professional
docker compose -f deploy/infra.yml -f deploy/monitoring.yml up -d
```

```yaml
# deploy/monitoring.yml
services:
  langfuse:
    image: langfuse/langfuse:latest
    ports: ["3000:3000"]
    environment:
      DATABASE_URL: postgresql://langfuse:${LANGFUSE_PG_PW}@postgres-langfuse/langfuse
      NEXTAUTH_SECRET: ${LANGFUSE_SECRET}
      SALT: ${LANGFUSE_SALT}
    depends_on: [postgres-langfuse]

  postgres-langfuse:
    image: postgres:16
    environment:
      POSTGRES_DB: langfuse
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: ${LANGFUSE_PG_PW}
```

### Integration (ab Phase 1)

```python
# core/workflow-engine/engine.py
from langfuse.callback import CallbackHandler

langfuse_handler = CallbackHandler(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ["LANGFUSE_HOST"],   # http://langfuse:3000 — lokal
)

result = await graph.ainvoke(
    state,
    config={"callbacks": [langfuse_handler], "configurable": {"thread_id": thread_id}},
)
```

**LangFuse liefert ab Tag 1:**
- LLM-Traces (Prompt, Response, Tokens, Latenz, Modell)
- Workflow-Steps (LangGraph-Nodes)
- FinOps pro Tenant und Modell (wichtig bei OpenRouter)
- Human-Feedback aus Console
- Evaluations + Datasets

**Wichtig:** LangFuse ist Observability, nicht Speicher. Persistenz bleibt P9 (G, A, L1, …).

**Monitor-Agent** (Platform, Phase 2): Service-Health + Audit in `ai_os_log` — läuft parallel zu LangFuse.

---

## 21. Produktions-Stack

Diese Komponenten gehören zum festgelegten AI-OS v2 Stack — phasenweise aktiviert, nicht austauschbar.

### 21.1 Backup & Disaster Recovery (Phase 2, Scheduler)

```bash
# backup.sh — täglich via Scheduler-Agent
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M)

# Postgres-Dump
docker exec postgres-platform pg_dump -U aios aios > /backup/postgres-$DATE.sql

# Qdrant-Snapshot
curl -X POST http://qdrant:6333/collections/content/snapshots
curl -X POST http://qdrant:6333/collections/skills/snapshots

# Letta-Export
docker exec letta python -m letta.export --output /backup/letta-$DATE.json

# Dateisystem
tar -czf /backup/knowledge-$DATE.tar.gz /opt/ai-os/content/ /opt/ai-os/customers/

# Zu Hetzner Storage Box (€3.49/Monat für 1 TB)
rsync -az /backup/ u123456@u123456.your-storagebox.de:/backups/ai-os/
```

```yaml
# Scheduler-Job für tägliches Backup
- id: daily-backup
  cron: "0 3 * * *"
  workflow: backup
  delivery: [monitor]   # Nur bei Fehler notifizieren
```

### 21.2 HTTPS / TLS — Caddy (Phase 5, Kunden-Deployment)

```yaml
# deploy/core.yml — Caddy als Reverse-Proxy
services:
  caddy:
    image: caddy:latest
    ports: ["80:80", "443:443"]
    volumes:
      - ./config/Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
```

```
# config/Caddyfile
abc.ai-os.app {
    reverse_proxy console-web:8092
    tls {
        # Automatisch Let's Encrypt — kein manuelles Zertifikat
    }
}
```

### 21.3 Push-Notifications — ntfy (Phase 2, in monitoring.yml)

Kunden erhalten sofortige Notifications auf ihr Handy wenn:
- Daily Briefing fertig
- Human-Review-Gate wartet
- Scheduler-Job fehlgeschlagen
- Service-Alert

```yaml
# deploy/monitoring.yml
services:
  ntfy:
    image: binwiederhier/ntfy:latest
    ports: ["7070:80"]
    volumes: ["ntfy_data:/var/cache/ntfy"]
    command: serve --cache-file /var/cache/ntfy/cache.db
```

```python
# sdk/mcp_adapter.py — ntfy als nativer MCP-Server
# POST http://ntfy:7070/{tenant_id}-alerts
# → Notification auf Handy (ntfy Android/iOS App, kostenlos)
```

### 21.4 Dokument-Verarbeitung — Docling (Phase 2, Ingest-Agent)

Ersetzt `pypdf` im Ingest-Worker. Docling versteht PDFs, Word, Excel, PowerPoint — inklusive Tabellen, Bilder, Layout:

```python
# platform-agents/ingest-agent/document_processor.py
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert(file_path)
# → Strukturierter Text + Tabellen + Metadaten
# → Deutlich besser als pypdf für Verträge, Rechnungen, Präsentationen
```

Besonders wertvoll für den Email-Agent (Rechnungen als PDFs) und den Research-Agent (Paper, Berichte).

### 21.5 Browser-MCP — Playwright (Phase 4, Research-Agent)

Für den Research-Agent: über SearXNG hinaus — strukturiertes Web-Scraping für Paywall-freie Seiten:

```python
# core/mcp-gateway/adapters/browser.py
# MCP-Server: browser
# Tools: navigate, extract_text, screenshot, fill_form
# Nutzt: playwright headless
# Sicherheit: Sandbox + Domain-Allowlist pro Tenant
```

### 21.6 Voice-Input — Whisper (Phase 6, Communications-Pack)

```yaml
# deploy/agents/communications.yml — Whisper Sidecar auf GPU-Hosts (GEX44)
services:
  whisper:
    image: onerahmet/openai-whisper-asr-webservice:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    ports: ["9000:9000"]
```

MCP-Adapter `speech-to-text`: Voice-Memos → Ingest → L1/L2.

### 21.7 Agent-zu-Agent — A2A-Protokoll (Phase 6, Multi-Instance)

`AgentBase` implementiert `a2a_endpoint` für Delegation zwischen AI-OS-Instanzen und externen Agenten — Standard: Google A2A über LangGraph.

---

## 22. Festgelegter Technologie-Stack

| Komponente | Technologie | Phase |
|------------|-------------|-------|
| OS | Ubuntu 26.04 LTS | 0 |
| Container | KVM-VM + Docker Compose | 0 |
| Datenbank | Postgres 16 + pgvector | 0 |
| Vektoren | Qdrant 1.x | 0 |
| Memory | Letta | 0 |
| LLM-Router | LiteLLM | 0 |
| Inference lokal | Ollama (qwen3.6-64k) | 0 |
| Inference Cloud | OpenRouter | 1 (Key) |
| Observability | LangFuse self-hosted | 0 |
| Websuche | SearXNG | 0 |
| Workflow | LangGraph + Postgres Checkpoints | 1 |
| Orchestrierung | FastAPI Orchestrator | 1 |
| Suche | Unified Search Service | 1 |
| Modellwahl | Model Gateway (sovereign/balanced/premium) | 1 |
| Konnektivität | MCP-Gateway | 1 |
| Agent-Contract | Pydantic v2 SDK + AgentBase | 3 |
| Console | Next.js 15 | 1–5 |
| TLS | Caddy | 5 |
| Notifications | ntfy | 2 |
| Dokumente | Docling | 2 |
| Web-Scraping | Playwright MCP | 4 |
| Voice | Whisper | 6 |
| Multi-Agent | A2A | 6 |

---

## 23. Inference: Ollama + OpenRouter

AI-OS v2 nutzt **zwei Inference-Kanäle** über LiteLLM (Cloud) bzw. Ollama direkt (Sovereign):

```
sovereign  →  Ollama LAN (Default, €0/Token, DSGVO) — /api/chat, think:false
balanced   →  OpenRouter Free / :floor (Cloud günstig)
premium    →  OpenRouter Free Frontier / Top-Modelle (Qualität)
coding     →  OpenRouter Free Coding (agentic Code — kein Alltags-Lagebild)
```

### Compute-Modi

| Modus | Route | Einsatz |
|-------|-------|---------|
| `sovereign` | Ollama LAN (`ai-os-sovereign` → qwen3.6-64k) | **Default** — PII, Standard-Tasks, Tagesübersicht-Hintergrund |
| `balanced` | OpenRouter (`ai-os-balanced`, DEV: nemotron-3-super-120b :free) | Längere Texte, allgemeine Wissensfragen |
| `premium` | OpenRouter (`ai-os-premium`, DEV: nemotron-3-ultra-550b :free) | Komplexe Analyse — Human-Review-Gate in PROD |
| `coding` | OpenRouter (`ai-os-coding`, poolside/laguna-m.1 :free) | Code-Generierung, Refactoring — **nicht** für „Was steht heute an“ |

**Fallbacks (LiteLLM):** `ai-os-balanced` / `ai-os-premium` / `ai-os-coding` → `ai-os-fallback` (`openrouter/free`).

### Routing-Regeln (deterministisch, in `intent_router.py` + `ai_os_router.py`)

1. Default: `sovereign` — immer Ollama (direkt, `think: false`)
2. Tagesfragen (`was steht heute an`, `steht heute an`, …) → Handler `daily_open_loops` (Brain, kein Cloud-LLM)
3. Keyword `linkedin`, `premium`, `blog-final` → `premium`
4. Metadata `tier=premium` → `premium`
5. Metadata `tier=balanced` → `balanced`
6. PII erkannt (Guardrails) → erzwingt `sovereign`, Cloud blockiert
7. PII + Anonymizer erfolgreich → `balanced` erlaubt

### OpenRouter-Konfiguration

| Feature | Nutzen |
|---------|--------|
| Unified API | Ein Key, 300+ Modelle über LiteLLM |
| Provider-Passthrough | Token-Preis = Anbieter-Preis |
| Automatische Fallbacks | Provider-Ausfall → `ai-os-fallback` |
| `:free` (DEV) / `:floor` (PROD) | Kostenoptimierung |
| Privacy-Settings | Provider ohne No-Training-Policy blockiert |

**Kosten:** ~5–7 % Overhead auf Cloud-Guthaben-Aufladung (5,5 % Karte). Token-Preise 1:1. Ollama: €0. `:free`-Modelle auf DEV = €0 Cloud (Rate-Limits beachten).

### LiteLLM-Konfiguration

```yaml
# config/litellm-config.yaml
model_list:
  - model_name: ai-os-sovereign
    litellm_params:
      model: openai/qwen3.6-64k:latest
      api_base: os.environ/OLLAMA_API_BASE   # http://${OLLAMA_HOST}:${OLLAMA_PORT}/v1
      api_key: dummy

  - model_name: ai-os-balanced
    litellm_params:
      model: openrouter/nvidia/nemotron-3-super-120b-a12b:free
      api_key: os.environ/OPENROUTER_API_KEY

  - model_name: ai-os-premium
    litellm_params:
      model: openrouter/nvidia/nemotron-3-ultra-550b-a55b:free
      api_key: os.environ/OPENROUTER_API_KEY

  - model_name: ai-os-coding
    litellm_params:
      model: openrouter/poolside/laguna-m.1:free
      api_key: os.environ/OPENROUTER_API_KEY

  - model_name: ai-os-fallback
    litellm_params:
      model: openrouter/openrouter/free
      api_key: os.environ/OPENROUTER_API_KEY

litellm_settings:
  fallbacks:
    - ai-os-balanced: ["ai-os-fallback"]
    - ai-os-premium: ["ai-os-fallback"]
    - ai-os-coding: ["ai-os-fallback"]
```

```env
OPENROUTER_API_KEY=sk-or-...
OLLAMA_HOST=192.168.178.64
OLLAMA_PORT=11434
DEFAULT_COMPUTE_MODE=sovereign
AIOS_COMPUTE_MODE_PATH=/opt/ai-os/memory/state/compute-mode.json
```

### DSGVO

- `balanced`/`premium`/`coding`: Daten verlassen das LAN → Guardrails + Anonymizer vor Cloud-Call
- LangFuse: Traces bleiben lokal in der VM
- OpenRouter: Prompts standardmäßig nicht geloggt
- Sovereign: Ollama LAN — kein Cloud-Outbound

---

*Dieses Dokument ist die einzige Implementierungsreferenz für AI-OS v2.*  
*Eine Entscheidung, ein Stack, keine Alternativen.*
