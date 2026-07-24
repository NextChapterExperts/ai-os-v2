# AI-OS v2 — Systemarchitektur

**Stand:** Juli 2026 (Platform-VM / P19 2026-07-24) · **Basis:** [v1 01-ARCHITEKTUR.md](../../1000-AI-OS/docs/platform/01-ARCHITEKTUR.md) + [19-OPTIMAL-ARCHITEKTUR.md](../../1000-AI-OS/docs/platform/19-OPTIMAL-ARCHITEKTUR.md)  
**Operativ:** [ROADMAP.md](../ROADMAP.md) · **Deployment:** [04-DEPLOYMENT.md](04-DEPLOYMENT.md) · **Platform-VM:** [11-PLATFORM-VM.md](11-PLATFORM-VM.md)  
**Bau-Ist:** [13-IST-STAND.md](13-IST-STAND.md) — Diagramme unten = **Zielbild**. Heute: Console + Orchestrator + MCP-Stubs + Cursor-Capture + Compose-Infra.

---

## Schichtenmodell

```
┌─────────────────────────────────────────────────────────────────────┐
│ SCHICHT 0 — HOST (nur Hypervisor)                                    │
│ KVM/libvirt · virt-manager — kein Cursor/AI-OS auf dem Host         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ VM-Console / Ports
┌────────────────────────────────▼────────────────────────────────────┐
│ PLATFORM-VM (Appliance) — DEV: + Cursor/Antigravity | PROD: headless│
│                                                                      │
│  SCHICHT 1 — CONSOLE :8092/:8093                                     │
│  Ebene 1 Lagebild · Ebene 2 Workflows · Ebene 3 Plattform          │
│  + Chat-Erfassung (Capture-Status)                                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ REST API
┌────────────────────────────────▼────────────────────────────────────┐
│ SCHICHT 2 — ORCHESTRATOR (OS-Kernel :8091)                          │
│                                                                      │
│  Intent-Router ─► Context-Builder (6 Slices) ─► Dispatch ─► Audit  │
│  [Deterministisch — kein LLM-Dispatch, kein LLM-Routing]           │
│  Memory Gateway (Inference + Persist) · Unified Search · Capture   │
│                                                                      │
│  ┌───────────────┐  ┌─────────────────┐  ┌────────────────────┐    │
│  │ Workflow-     │  │  Skill-Service  │  │  Scheduler         │    │
│  │ Engine        │  │  :8095          │  │  :8096             │    │
│  │ (LangGraph)   │  │  Loop+Store     │  │  Cron+NLP          │    │
│  └───────────────┘  └─────────────────┘  └────────────────────┘    │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────────┘
       │          │          │          │          │
  ┌────▼──┐  ┌───▼────┐  ┌──▼────┐  ┌──▼────┐  ┌──▼───────────────┐
  │ MCP-  │  │ Pipe-  │  │Ingest │  │Memory │  │ Guardrails-Agent │
  │ Gate- │  │ line-  │  │-Agent │  │-Agent │  │ Monitor-Agent    │
  │ way   │  │ Agent  │  │       │  │       │  │                  │
  │ :8097 │  │        │  │       │  │L1/2/3 │  │                  │
  └────┬──┘  └────────┘  └───────┘  └───────┘  └──────────────────┘
       │
  ┌────▼──────────────────────────────────────────────────────────┐
  │ SCHICHT 3 — MCP-SERVER                                        │
  │ Nativ: mail · cms · drive · web · kg · memory · console       │
  │ Extern (Sidecar): github · vercel · calendar (M2/M3)          │
  └────┬──────────────────────────────────────────────────────────┘
       │
  ┌────▼──────────────────────────────────────────────────────────┐
  │ SCHICHT 4 — DATENSCHICHT (souverän, in der VM)                │
  │                                                                │
│  L0  YAML schema/        — Entity/Edge (+ org-brain / P18)    │
│  K   content/ knowledge/ — Kanonische Dateien (Company Brain) │
│  G   Postgres kg_*       — Knowledge Graph (platform+org+SKU) │
│  L1  Qdrant              — Vektor-Index (kuratiert)           │
│  L2  Letta Archival      — Episoden (Agent-Memory, nicht SSOT)│
│  L3  Letta Core          — Profil; Claims nur via DP → G      │
  │  SK  SQLite + Qdrant     — Skill-Loop-Store                   │
  │  A   Postgres ai_os_log  — Audit (unveränderlich)             │
  └────┬──────────────────────────────────────────────────────────┘
       │
  ┌────▼──────────────────────────────────────────────────────────┐
  │ SCHICHT 5 — MEMORY GATEWAY (Inference + Persist-Hook)         │
  │ LiteLLM :4000 → Ollama LAN · OpenRouter — immer mit Memory-Trail│
  └───────────────────────────────────────────────────────────────┘
```

---

## Kernkomponenten

### Orchestrator (OS-Kernel)

**Aufgabe:** Deterministisches Herz des Systems. Empfängt jeden Intent, baut Context Bundle, routet zum Workflow.

```
POST /v1/dispatch
  └─► intent_router      → Workflow-Name bestimmen (Registry)
  └─► context_resolution → 6 Slices bauen
  └─► skill_loader       → relevante Skills laden
  └─► guardrails_check   → Policies + PII vorab prüfen
  └─► workflow_engine    → LangGraph-Graph starten
  └─► audit              → AgentRun committen

POST /v1/dataproduct/commit   → DP in G + K + ggf. L1
GET  /v1/dataproduct/resolve  → DP aus G laden
POST /v1/context/resolve      → Context Bundle debuggen
GET  /v1/scheduler/jobs       → Scheduler-Jobs anzeigen
POST /v1/scheduler/jobs       → Neuen Cron-Job anlegen
```

**Strenge Regel:** Kein LLM-Call im Orchestrator außer für Context-Enrichment (Embedding). Routing = Code.

---

### Workflow-Engine (LangGraph)

**Aufgabe:** Stateful, checkpointete Ausführung von Multi-Step-Workflows.

```python
# Jeder Workflow = LangGraph StateGraph
# Jeder Node = atomarer, idempotenter Schritt
# Checkpoints in Postgres — Workflow nach Neustart fortsetzbar
# interrupt() für Human-in-the-Loop

Workflow-Typen:
  sequential:   A → B → C → END
  parallel:     A → [B, C] → D → END (Fan-out)
  conditional:  A → B → {cond: C | D} → END
  human-loop:   A → B → interrupt() → C → END
```

---

### SDK (Agent-Contract)

**Aufgabe:** Erzwingt Plattform-Konformität bei jedem Agenten.

```python
class MyAgent(AgentBase[MyInput, MyOutput]):
    agent_id = "my-agent"           # Pflicht
    version = "1.0.0"               # Pflicht
    input_schema = MyInput          # Pflicht
    output_schema = MyOutput        # Pflicht

    async def run(self, input_dp: MyInput) -> MyOutput:
        # Nur self.mcp für externe Calls
        # Nur self.ctx für Tenant-Kontext + LLM
        ...
```

→ Details: [02-AGENT-SDK.md](02-AGENT-SDK.md)

---

### MCP-Gateway

**Aufgabe:** Einziger erlaubter Konnektivitätskanal. Allowlist + Caps + Audit.

```
Agent → self.mcp.call("web_search", "search", {...})
             ↓
        MCPAdapter → POST /v1/call an MCP-Gateway
             ↓
        MCP-Gateway: tenant-check + cap-check + route
             ↓
        Native Adapter (web_search, mail, cms, ...) oder External Sidecar
             ↓
        Ergebnis + Audit-Log-Eintrag
```

---

### Skill-Loop

**Aufgabe:** System wird mit jeder Nutzung klüger.

```
Task abgeschlossen
  └─► skill_hook.post_run()
  └─► Komplexitäts-Heuristik (>3 Steps, >30s, >3 MCP-Calls)
  └─► Skill-Distiller: LLM destilliert Ablauf → Markdown-Skill-Dokument
  └─► Skill-Store: save (Markdown + Qdrant + FTS5)

Nächster Request mit ähnlichem Intent
  └─► skill_loader.find_relevant(intent, tenant_id)
  └─► Skill-Dokument in SkillSlice des Context Bundle
  └─► Agent bekommt «Wie wurde das zuletzt gelöst?» als Kontext

Nach 5. Wiederholung
  └─► skill_refiner: Skill verbessern auf Basis neuer Erfahrungen
  └─► Skill-Version +1, SUPERSEDES-Edge im KG
```

→ Details: [ROADMAP.md §14](../ROADMAP.md#14-skill-loop-im-detail)

---

### Memory-Flywheel

```
Jede Aktion → DP-Commit → G (KG) + K (files) + ggf. L1

Täglich (L2-Curator, 02:00 Uhr via Scheduler):
  L1-Chunks (24h) → LLM-Verdichtung → Letta Archival Memory (L2)
  (= episodisch / Agent-Runtime — nicht Company-Brain-SSOT)

Wöchentlich (L3-Curator, Montag 03:00):
  Letta Archival (7d) → Fakten-Extraktion
  → OrgClaim DataProduct → DP-Commit → G (org:Claim)
  → kein Direkt-Write Letta→kg_* (P8/P9/P18)

Nach komplexem Task (Skill-Distiller):
  AgentRun → LLM-Skill-Destillation → Skill-Store (SK)

Ergebnis: Jede Nutzung macht das System klüger, ohne manuellen Aufwand.
```

### Company Brain (P18)

**SSOT für Mandantenwissen** = K + G (`org:*` + Fach-SKU-Typen) + kuratiertes L1.  
**Letta** = Agent-Gedächtnis (Working/Tactical/L2/L3), Quelle für Destillation — nicht die Firmenwahrheit.

- Agenten **lesen** über MCP `kg` / Unified Search; **schreiben** nur als DataProduct → Commit.
- **Query-Router** vor Suche (nicht alle Schichten blind); **Claim-Härte**; **atomarer G+K-Commit**.
- Ontologie, Gates, Optimierungen: [09-COMPANY-BRAIN.md §12](09-COMPANY-BRAIN.md#12-betriebsoptimierungen-verbindlich) · ROADMAP §12.4.7 · [10-MEMORY-EINFACH.md](10-MEMORY-EINFACH.md).

### Platform-VM + Memory Gateway (P19)

- Erstes Lizenzprodukt: **VM + `AIOS-CORE`** — [11-PLATFORM-VM.md](11-PLATFORM-VM.md).
- Alle LLM-Calls über **Memory Gateway**; externe Chats (Gemini, Antigravity, …) über **Chat Capture** → gleicher Speicher.
- **DEV-VM:** Cursor + Antigravity in der VM · **PROD-VM:** nur Browser.

```
│  L0  YAML schema/        — Entity/Edge-Definitionen (+ org-brain)   │
│  K   content/ knowledge/ — Kanonische Dateien (SSOT)                │
│  G   Postgres kg_*       — Knowledge Graph inkl. org:*              │
│  L1  Qdrant              — nur kuratiert/published                  │
│  L2  Letta Archival      — Episoden (nicht SSOT)                    │
│  L3  Letta Core          — Profil; Claims nur via DP → G            │
```

---

## Context Bundle (6 + 1 Slices)

```python
ContextBundle:
  SystemSlice:    tenant_id · compute_mode · guardrails_policy · brand_context
  DomainSlice:    KG-Traversal 1-2 Hops via MCP kg (org:* priorisiert, P18)
  TaskSlice:      intent_params · input_dp_refs · workflow_name
  RetrievalSlice: L1 Qdrant (top-k) + GraphRAG (Phase 6)
  EpisodicSlice:  letzte 3 AgentRuns · Letta User-Modell
  GuardrailSlice: aktive Policies · PII-Grenzen · Compliance-Flags
  SkillSlice:     (NEU v2) top-3 relevante Skill-Dokumente
```

**Merksatz:** Ein Agent bekommt nie mehr als nötig — aber immer genau das, was er braucht.

---

## Tenant-Isolation (Runtime)

```python
TenantContext:
  qdrant_namespace:  f"tenant_{tenant_id}"  → keine Cross-Tenant-Suche möglich
  letta_project_id:  per Tenant                → isoliertes episodisches Gedächtnis
  kg_partition:      tenant_id               → alle KG-Queries mit WHERE tenant_id = ?
  litellm_budget_id: per Tenant              → isolierte Budget-Kontrolle
  guardrails_policy: per Tenant              → eigene Compliance-Regeln möglich
  active_packages:   List[str]               → nur installierte SKUs nutzbar
```

---

## Unterschied zu v1

| Komponente | v1 | v2 |
|-----------|----|----|
| Workflow-Runner | Eigener Python-Code | LangGraph StateGraph |
| Agent-Contract | Optional, umgehbar | SDK erzwingt bei Instanziierung |
| Skill-Loop | P1-Baustelle offen | Phase 1 eingebaut |
| Scheduler | P2-Blocker | Phase 2 eingebaut |
| Memory L2/L3 | Teilweise | Vollständiges Flywheel |
| Tenant-Isolation | Ordnerstruktur | Runtime (Namespace, Projekt, Budget) |
| Deployment | Monolith | 3 unabhängige Modi |
| Context Bundle | CTX1-3 | CTX1-7 (+ SkillSlice) |
| GraphRAG | Gespeichert, kein Retrieval | RetrievalSlice kombiniert Vektor + Graph |
