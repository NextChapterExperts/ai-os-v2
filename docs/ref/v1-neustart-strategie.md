# AI-OS — Neustart-Strategie: Freeze v1 + Build v2

**Stand:** Juli 2026 · **Nr. 20** · **Autor:** Peter / NCE  
**Status:** Entscheidungsvorlage — noch nicht beschlossen  
**Verwandte Dokumente:** [19-OPTIMAL-ARCHITEKTUR.md](19-OPTIMAL-ARCHITEKTUR.md) · [18-FRAMEWORK-VERGLEICH.md](18-FRAMEWORK-VERGLEICH.md) · [00-VISION.md](00-VISION.md)

---

## Ausgangslage

Der aktuelle AI-OS-Stack (v1) ist ein funktionierender Pilot mit echtem produktivem Nutzen. Gleichzeitig zeigt er die typischen Symptome eines iterativ gewachsenen Systems:

- **UI zu unübersichtlich und zu detailliert** — Console versucht alles zu zeigen; Ebene-3-Infrastruktur-Details landen in Ebene-1-Screens.
- **Kern-Differenzierung nicht sichtbar** — Die wirklich wertvollen Architektur-Entscheidungen sind da, aber vergraben.
- **Kein durchgesetzter Contract** — Agenten *können* Datenprodukte liefern, aber kein Layer *erzwingt* es.
- **Multi-Tenant im Code, nicht in der Laufzeit** — Struktur in `packages/` und `customers/`, aber keine echte Runtime-Isolation.
- **Alles ein Monolith** — Platform, Platform-Agenten und Fach-Agenten sind im Docker-Compose nicht separierbar.

Die Frage ist: **Refactor im bestehenden Repo** oder **Freeze v1 + neues Projekt v2**?

---

## Warum Freeze + Neustart sinnvoller ist als Refactoring

| Argument | Refactor in v1 | Neustart v2 |
|---|---|---|
| Gewachsene Komplexität | Bleibt — jede Änderung kämpft gegen die Vergangenheit | Sauberer Schnitt |
| SDK-Contract durchsetzen | Schwer rückwirkend — jeder Agent müsste angefasst werden | Von Tag 1 Pflicht |
| UI neu denken | Möglich, aber Kompromisse mit bestehendem BFF | Freie Information Architecture |
| Wertvolles erhalten | Muss vorsichtig migriert werden | Bewusstes Übernehmen, kein Schleppen |
| Mentale Klarheit | Alt und Neu vermischen sich | Klare Grenze: alt = Referenz, neu = Zukunft |
| Risiko | Hoch — funktionierende Teile kaputtmachen | Mittel — Feature-Parität braucht Zeit |

**Entscheidendes Argument:** Ohne einen neuen Start mit dem SDK-Contract-Ansatz baut man in 6 Monaten wieder dasselbe. Der Contract ist der eigentliche Kern — nicht die Infrastruktur.

---

## Was v1 geleistet hat (und erhalten bleibt)

v1 ist kein Misserfolg — es ist die Lernphase, die v2 erst möglich macht. Folgendes bleibt als **Read-only-Referenz** vollständig erhalten:

✅ Infrastruktur-Know-how (Incus + Docker, Netzwerk, Deployment)  
✅ 45 Tests — werden zur Spezifikation für v2  
✅ Alle Python-Tool-Module (`mcp_gateway`, `embed`, `qdrant`, `kg`, `guardrails`, …)  
✅ Workflow-Definitionen (daily-briefing, research, blog-pipeline)  
✅ Agenten-Konfigurationen (nextchapter, platform-test)  
✅ Bewiesene Infrastruktur: Qdrant, Letta, LiteLLM, Postgres, SearXNG  
✅ MCP-Adapter für mail, cms, drive, web, kg, memory  
✅ Docs 00–19 — bleiben vollständig, kein Löschen  

---

## Das Kern-Prinzip von v2

> **Jeder Agent ist ein Contract, kein Skript.**

v1-Problem: Agenten *können* Datenprodukte und MCP benutzen — aber nichts *zwingt* sie dazu. Das führt zu inkonsistenten Datenflüssen und einer Plattform, die ihre eigenen Prinzipien nicht durchsetzt.

v2-Lösung: Ein **Agent-SDK** definiert den Contract. Ein Agent, der ihn nicht erfüllt, ist kein gültiger AI-OS-Agent und wird nicht installiert.

```
┌─────────────────────────────────────────────────────────┐
│  Agent-Contract (jeder Agent muss das erfüllen)         │
│                                                         │
│  1. Input:  Typisiertes Datenprodukt (DP) aus L1–L3    │
│  2. Output: Typisiertes Datenprodukt (DP) → L1–L3      │
│  3. Tool-Calls: ausschließlich über MCP                 │
│  4. Skill-Hook: optional, aber standardisiert           │
│  5. Tenant-Kontext: immer explizit übergeben            │
└─────────────────────────────────────────────────────────┘
```

---

## Ziel-Struktur v2

```
ai-os-v2/
│
├── core/                          # Das OS — läuft ohne jeden Agenten
│   ├── orchestrator/              # Intent-Router · Context-Builder · Audit
│   ├── workflow-engine/           # LangGraph-basiert · Checkpoint · Human-in-Loop
│   ├── skill-service/             # Skill-Loop · Skill-Store · Index
│   ├── scheduler/                 # Cron · Natural-Language-Scheduling · Delivery
│   ├── mcp-gateway/               # Einziger Konnektivitäts-Layer (M1 nativ + M2 Sidecar)
│   ├── memory/                    # L1 Curator · L2 Curator · L3 Curator
│   ├── guardrails/                # L1/L2/L3 · PII · Policies
│   ├── monitor/                   # Services · Runs · FinOps · Alerts
│   └── console/                   # Next.js — 3-Ebenen-IA (Lagebild / Workflows / Plattform)
│
├── sdk/                           # Agent-SDK — Contract für jeden Agenten
│   ├── agent_base.py              # Basisklasse: Input-DP, Output-DP, MCP, Tenant-Kontext
│   ├── dataproduct.py             # Datenprodukt-Schema + Validator (aus v1 übernommen)
│   ├── mcp_adapter.py             # MCP-Wrapper — kein direktes HTTP aus Agenten
│   ├── skill_hook.py              # Skill-Destillation nach Task
│   ├── agent_template/            # Scaffolding für neuen Agenten (1 Befehl)
│   └── tests/                     # Contract-Tests — jeder Agent muss sie bestehen
│
├── platform-agents/               # OS-Schicht — separat deploybar
│   ├── pipeline-agent/            # RAG-Pipeline
│   ├── ingest-agent/              # Inbox-Polling
│   ├── memory-agent/              # Curators L1/L2/L3
│   ├── guardrails-agent/          # Policy-Enforcement
│   ├── monitor-agent/             # Observability
│   └── scheduler-agent/           # Cron-Runner (NEU)
│
├── agents/                        # Fach-Agenten — installierbar als SKU-Pakete
│   ├── research/                  # AIOS-PACK-RESEARCH — aus v1 übernommen
│   ├── blog/                      # AIOS-PACK-BLOG
│   ├── email/                     # AIOS-PACK-EMAIL
│   ├── time/                      # AIOS-PACK-TIME
│   └── news/                      # AIOS-PACK-NEWS
│
├── customers/                     # Tenant-Profile — unverändert aus v1
│   ├── _template/
│   ├── nextchapter/
│   └── platform-test/
│
└── docs/                          # Neue Dokumentation — klar und minimal
    ├── 00-VISION.md               # Unverändert aus v1
    ├── 01-ARCHITEKTUR.md          # v2-Architektur (dieses Konzept)
    ├── 02-AGENT-SDK.md            # Contract — wie schreibt man einen Agenten?
    ├── 03-DATENPRODUKTE.md        # Schema-Catalog + Datenflüsse
    └── 04-DEPLOYMENT.md           # Core · Platform-Agents · Fach-Agenten separat
```

---

## Die drei Deployment-Modi

Das ist der entscheidende Unterschied zu v1: Platform, Platform-Agenten und Fach-Agenten sind **einzeln deploybar**.

```
Modus 1 — Core only (minimales OS)
  docker-compose -f core.yml up
  → Orchestrator, Workflow-Engine, MCP-Gateway, Console
  → Kein Agent, kein Memory-Curator, kein Scheduler

Modus 2 — Core + Platform-Agenten (vollständige Plattform)
  docker-compose -f core.yml -f platform-agents.yml up
  → + Pipeline, Ingest, Memory, Guardrails, Monitor, Scheduler

Modus 3 — Full (Plattform + Fach-Agenten)
  docker-compose -f core.yml -f platform-agents.yml -f agents/{research,blog,email}.yml up
  → Vollständiger Stack für einen Tenant
```

Jeder Deployment-Modus ist eigenständig lauffähig und testbar.

---

## Datenprodukt als Kern-Kontrakt

Das ist die sichtbarste Lücke in v1 — und das wichtigste Konzept in v2.

### Was ein Datenprodukt ist

```python
# Jeder Agent hat genau diese Signatur:
class BlogDraftProduct(DataProduct):
    schema_version: str = "1.0"
    tenant_id: str
    produced_by: str           # Agent-ID
    produced_at: datetime
    workflow_run_id: str       # Traceability

    # Domänen-Payload
    title: str
    body: str
    sources: list[str]
    compliance_status: Literal["cleared", "pending", "blocked"]
    target_channel: str

# Gespeichert in L1/L2/L3 je nach Retention-Regel:
#   L1 (Qdrant)  — suchbar, 90-Tage-Rolling
#   L2 (Letta)   — episodisch, dauerhaft
#   L3 (KG)      — als Graph-Knoten mit Beziehungen
```

### Warum das die Plattform sichtbar besser macht

1. **Observability:** Console kann jeden Datenfluss als DP-Stream anzeigen — kein Raten mehr, was welcher Agent produziert hat.
2. **Qualitätskontrolle:** Guardrails validiert das DP-Schema bevor es gespeichert wird — kein Schmutz in L1.
3. **Composability:** Agenten können die Outputs anderer Agenten konsumieren ohne Implementierungsdetails zu kennen.
4. **Debugging:** Jeder Fehler ist einem DP + Workflow-Run + Tenant zuordenbar.

---

## Die neue Console — 3-Ebenen-Information-Architecture

v1-Problem: Ebene-3-Infrastruktur-Details (Pipeline-Innenleben, Agent-Rohdaten, Config-Dumps) landen in Ebene-1-Screens.

```
Ebene 1 — Lagebild (täglich, 80 % der Nutzung)
  ┌──────────────────────────────────────────┐
  │  Was ist heute passiert?                 │
  │  Briefing · Neue Datenprodukte · Alerts  │
  │  Offene Tasks · Skill-Vorschläge         │
  └──────────────────────────────────────────┘

Ebene 2 — Workflows (wöchentlich, 15 % der Nutzung)
  ┌──────────────────────────────────────────┐
  │  Welche Workflows laufen?                │
  │  Status · Output-DPs · Qualität          │
  │  Scheduler · Human-in-the-Loop-Queue     │
  └──────────────────────────────────────────┘

Ebene 3 — Plattform (selten, 5 % der Nutzung)
  ┌──────────────────────────────────────────┐
  │  Infrastruktur · Agenten-Config          │
  │  MCP-Server · Guardrails-Policies        │
  │  FinOps · Knowledge Graph · Skills       │
  │  → Nur wenn etwas kaputt ist oder neu    │
  │    konfiguriert werden muss              │
  └──────────────────────────────────────────┘
```

Alles was heute in Ebene-1-Screens steht, aber eigentlich Ebene-3-Information ist — fliegt raus.

---

## Migrations-Strategie

### Phase 0 — v1 einfrieren (1 Tag)
- Git-Tag `v1-freeze` auf aktuellem Commit
- README-Hinweis: «v1 — Read-only-Referenz»
- Kein weiteres Feature-Development in v1
- Betrieb bleibt aktiv (nextchapter läuft weiter auf v1)

### Phase 1 — Core + SDK (2–3 Wochen)
- Neues Repo `ai-os-v2` anlegen
- Core-Dienste: Orchestrator, Workflow-Engine (LangGraph), MCP-Gateway, Console-Skeleton
- SDK schreiben: `agent_base.py`, `dataproduct.py`, `mcp_adapter.py`
- Contract-Tests: jeder neue Agent muss sie bestehen
- Docker-Compose Modus 1 lauffähig

### Phase 2 — Platform-Agenten (2 Wochen)
- Pipeline-Agent, Ingest-Worker, Memory-Agent (L1/L2/L3)
- Guardrails-Agent (L1/L2/L3 inkl. PII)
- Scheduler-Agent (war P2-Blocker in v1)
- Monitor-Agent
- Docker-Compose Modus 2 lauffähig

### Phase 3 — Fach-Agenten (2–3 Wochen)
- Research-Agent (aus v1 übernehmen, SDK-Contract anpassen)
- Email-Agent (aus v1 übernehmen)
- Blog-Agent (Content Factory vollständig in v2)
- Docker-Compose Modus 3 lauffähig

### Phase 4 — Tenant-Migration (1 Woche)
- nextchapter-Konfiguration auf v2 migrieren
- v1-Betrieb abschalten
- Skill-Loop produktiv schalten

**Gesamt-Aufwand:** ca. 8–10 Wochen bis v2 Feature-Parität mit v1 hat — mit besserem Fundament.

---

## Was in v2 explizit NICHT gemacht wird

Bewusste Scope-Begrenzung um den Start nicht zu versenken:

- Kein Multi-Cloud-Deployment (weiterhin Incus lokal)
- Kein öffentliches Multi-Tenant-SaaS (weiterhin self-hosted pro Installation)
- Keine neue Inference-Infrastruktur (LiteLLM + externer Ollama bleibt)
- Kein UI-Framework-Wechsel (Next.js 15 bleibt)
- Kein Neo4j-Wechsel erzwungen (Postgres-KG oder Neo4j — separate Evaluierung)
- Langflow bleibt optional

---

## Entscheidungskriterien

**Neustart v2 ist richtig wenn:**
- [ ] Die Kernprinzipien (DP-Contract, Multi-Tenant-Runtime, separierbare Deployment-Modi) sind in v1 nicht sauber nachzurüsten
- [ ] Der Aufwand für gezielten Refactor in v1 ist vergleichbar mit einem Neustart
- [ ] v1 läuft stabil genug, dass während v2-Entwicklung kein Notfall-Eingriff nötig ist
- [ ] Die mentale Klarheit eines sauberen Starts wird höher bewertet als der Komfort des Bekannten

**Gezielter Refactor in v1 ist besser wenn:**
- [ ] Die Zeit für Feature-Parität in v2 nicht vertretbar ist
- [ ] Es kurzfristig einen Kundenbedarf gibt, der nicht warten kann
- [ ] Die UI-Probleme durch ein gezieltes Design-Sprint in v1 lösbar sind

---

## Zusammenfassung

v1 hat das Fundament gelegt. v2 baut es mit den richtigen Prinzipien von Grund auf:

| | v1 | v2 |
|---|---|---|
| Agent-Contract | Optional | Pflicht (SDK) |
| Datenprodukte | Möglich | Erzwungen |
| Multi-Tenant Runtime-Isolation | Struktur | Laufzeit |
| Deployment-Modi | Monolith | Core / Platform / Agents trennbar |
| UI Information Architecture | Alles sichtbar | 3 Ebenen, klare Trennung |
| Workflow-Engine | Eigener Runner | LangGraph (bewährt) |
| Skill-Loop | Offen (P1) | Von Tag 1 eingebaut |
| Scheduler | Offen (P2) | Von Tag 1 Phase 2 |
| Sichtbarkeit der Kernprinzipien | Vergraben | Explizit im SDK |
