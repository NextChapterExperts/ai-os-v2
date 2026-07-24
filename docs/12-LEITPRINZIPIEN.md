# AI-OS v2 — Leitprinzipien (P1–P19) im Detail

**Stand:** 2026-07-24 · **Verbindlich** · Kurzliste: [00-VISION.md](00-VISION.md) · Bauanleitung: [../ROADMAP.md](../ROADMAP.md) Kap. 1  

Jedes Prinzip hat: **Intent · Regeln · Verboten · Wo im System · Abnahme**.  
Verletzung = Architekturfehler, kein „Style-Hinweis“.

---

## Übersicht

| | Prinzip | Kern in einem Satz |
|--|---------|-------------------|
| P1 | Kontextsystem vor Agenten | Pro Dispatch ein gebautes Context Bundle — kein Prompt-Müllhaufen |
| P2 | Nicht alles speichern | Schicht + Typ bestimmen Speicherziel — nie das LLM |
| P3 | Graph vor reinem RAG | Beziehungen leben in G, nicht nur als Embedding-Ähnlichkeit |
| P4 | Determinismus in der Hülle | Infrastruktur-Entscheidungen = Code; LLM = Facharbeit |
| P5 | MCP als einzige Konnektivität | Agenten sprechen die Welt nur über `self.mcp` an |
| P6 | Skill-Loop | Erfolgreiche Arbeit wird zu versioniertem Skill, nicht zu Copy-Paste |
| P7 | State-Machine | Workflows = LangGraph, checkpointed, replaybar |
| P8 | Agent-Contract | Ohne SDK-Contract kein Agent |
| P9 | Alles in die Datenbank | Kein Workflow-Ende nur im RAM/Log |
| P10 | Platform vor Fach-Agenten | Gate grün, dann erst SKUs |
| P11 | Unified Search + Memory Gateway | Eine Suche, eine Inference-Tür — Platform-Kern |
| P12 | FinOps by Design | Default lokal; Cloud sichtbar, messbar, begründet |
| P13 | Qualität durch Kontext | Erst Kontext verbessern, dann teureres Modell |
| P14 | Ein Stack, alle Tiers | Dev→Enterprise = gleiche Compose-Architektur |
| P15 | PGE-Trinity | Plan → Gatekeeper(Code) → Execute |
| P16 | Observer Audit | Lokaler Qualitätscheck nach Antworten |
| P17 | Hash-Audit | Unveränderliche Kette + Run-Receipts |
| P18 | Company Brain | Firmen-SSOT ≠ Agent-Memory ≠ persönlicher Second Brain |
| P19 | Platform-VM first | Erstes Produkt = VM + Core; eine Tür, ein Gedächtnis |

---

## P1 — Kontextsystem vor Agenten

**Intent:** Der Agent bekommt nicht „alles“, sondern ein **gezieltes Bundle**. Qualität kommt aus Kontextbau, nicht aus längerem Prompt.

**Regeln**
- Jeder `dispatch` / Workflow-Start erhält ein **Context Bundle** mit festen Slices:
  - `SystemSlice` — Tenant, Compute-Modus, Policies, Brand
  - `DomainSlice` — KG-Traversal (1–2 Hops, `org:*` priorisiert)
  - `TaskSlice` — Intent, Input-DP-Refs, Workflow-Name
  - `RetrievalSlice` — Unified Search (L1 + ggf. G/SK)
  - `EpisodicSlice` — letzte Runs / relevantes Letta
  - `GuardrailSlice` — aktive Policies, PII-Grenzen
  - `SkillSlice` — top-n passende Skills (P6)
- Bundle-Bau ist **Orchestrator-/Platform-Code**, nicht Agent-Selbstbedienung.
- Token-Budgets pro Slice sind konfigurierbar; Overflow → Kürzen nach Priorität, nicht „alles anhängen“.

**Verboten**
- Agent lädt selbst „die ganze Inbox“ oder alle Qdrant-Hits in den Prompt.
- Fach-Agent baut eigenes RAG parallel zum Context-Builder.

**Wo:** `core/orchestrator/context_resolution.py` · docs Context Bundle in [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md)

**Abnahme:** Dispatch-Response enthält `context_bundle` mit allen Slice-Keys; ohne Bundle kein LLM-Call.

---

## P2 — Nicht alles speichern

**Intent:** Speicher ist teuer an Qualität, nicht nur an Disk. Rohdaten ≠ Wahrheit.

**Regeln (Schichtregeln)**

| Schicht | Darf rein | Darf nicht rein |
|---------|-----------|-----------------|
| **K** | Kanonische Dateien, Entwürfe in `pipeline/`, Seed | Beliebige Chat-Dumps als „Wahrheit“ |
| **L1** | Nur **published / kuratiert** Embeddings | Roh-Chat, Drafts, Secrets |
| **G** | Typisierte Entities/Edges inkl. `org:*` | Freitext ohne Schema |
| **L2** | Episoden (was passierte) | Decisions als Roh-Chat |
| **L3** | Profil-Fakten | Ungeprüfte Claims ohne Curator |
| **A** | Jeder relevante Run/Tool-Call | — (Pflicht) |
| **SK** | Destillierte Skills nach Erfolg | Fehlgeschlagene Experimente ungefiltert |

- **LLM entscheidet nie** `storage_target` — das macht Schema/DP-Service (P4/P8).

**Verboten:** „Alles indexieren“; Draft → L1; Chat → `org:Decision` ohne Gate.

**Wo:** [03-DATENPRODUKTE.md](03-DATENPRODUKTE.md) · [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md) · [10-MEMORY-EINFACH.md](10-MEMORY-EINFACH.md)

**Abnahme:** Curator-/Commit-Tests: Draft bleibt außerhalb L1; published landet in L1.

---

## P3 — Graph vor reinem RAG

**Intent:** „Wer hat was entschieden / womit hängt das zusammen?“ braucht **Kanten**, nicht nur Cosine-Similarity.

**Regeln**
- Fachliche Beziehungen (Serie→Publish, Person→Meeting→Offering, Claim→Blog) als **Edges in G**.
- Unified Search darf Vektoren nutzen, muss aber **Graph-Traversal / Score-Fusion** können.
- Neue Entitätstypen nur über **L0-Schema** (`platform:*` / `org:*` / SKU).

**Verboten:** Nur Vektor-DB als „Knowledge Base“; Beziehungen nur in Markdown-Links ohne G.

**Wo:** Postgres `kg_*` · MCP `kg` · GraphRAG Phase 6

**Abnahme:** Abnahmefrage à la „Welche Decisions hängen am Offering X?“ antwortbar über G, nicht nur Keyword-Suche.

---

## P4 — Determinismus in der Hülle

**Intent:** Das OS darf nicht „kreativ“ über Sicherheit, Routing, FinOps entscheiden.

**Regeln — Code (kein LLM)**
- Intent-Routing / Dispatch-Ziel
- Guardrails / PGE-Gatekeeper (P15)
- Audit-Schreiben / Hash-Chain (P17)
- Speicherziel laut Schema
- Compute-Modus-Policy (wann Cloud erlaubt)
- License-/SKU-Checks

**LLM darf**
- Texte, Analysen, Pläne (Planner), Zusammenfassungen, Extraktion **innerhalb** freigegebener Tools

**Verboten:** LLM wählt Tenant; LLM umgeht Allowlist; LLM setzt `storage_target`.

**Wo:** Orchestrator, MCP-Gateway, DP-Service, Gatekeeper

**Abnahme:** Unit-Tests ohne LLM für Dispatch/Guardrails; bei LLM-Ausfall bleiben Policy-Entscheidungen reproduzierbar.

---

## P5 — MCP als einzige externe Konnektivität

**Intent:** Eine kontrollierte Tür nach draußen — auditierbar, begrenzt, allowlisted.

**Regeln**
- Agenten nur `self.mcp.call(server, tool, args)`.
- Gateway: **Allowlist** pro Tenant/Agent, **Caps** (Rate/Größe), **Audit** jedes Calls.
- Native Server mind.: `mail`, `cms`, `drive`, `web`, `kg`, `memory`, `console` (laut Roadmap).

**Verboten**
- `httpx`/`requests`/`smtp` direkt im Fach-Agenten
- API-Keys in Agent-Code statt in MCP-Server-Config

**Wo:** `core/mcp-gateway` · SDK `mcp_adapter.py`

**Abnahme:** Contract-Test: Agent ohne MCP-Adapter startet nicht; direkter HTTP-Import in `packages/*-agent` = CI-Fail (Lint/Arch-Test).

---

## P6 — Skill-Loop statt statischer Skripte

**Intent:** Wiederkehrende Arbeit wird zum **Skill** (Wissen + Ablauf), nicht jedes Mal neu erfunden.

**Regeln**
- Nach komplexem erfolgreichen Task: Skill-Distiller → Markdown-Skill + Metadaten (Version, Tags, success_rate).
- Skills indexiert (FTS + Vektor) und im **SkillSlice** (P1) geladen.
- Bei Wiederholung: Skill anwenden → Ergebnis → Skill verfeinern (Version++).

**Verboten:** Skills nur als lose Notizen ohne Index; Skills ohne Bezug zu Tenant.

**Wo:** `skill-service` · Tabelle `skills` · SkillSlice

**Abnahme:** Zweiter gleichartiger Task lädt bestehenden Skill (Trace/Log belegt `skill_id`).

---

## P7 — Orchestrierung als State-Machine

**Intent:** Lange Prozesse sind Graphen mit Zustand — nicht verschachtelte Scripts.

**Regeln**
- Workflows = **LangGraph**; Nodes atomar, möglichst idempotent.
- Checkpoints in Postgres (`workflow_checkpoints`).
- Fehler → klarer State + Retry/Resume, nicht „Thread gestorben, Kontext weg“.

**Verboten:** Eigener ad-hoc Runner parallel zu LangGraph; Workflow-State nur im RAM.

**Wo:** `core/workflow-engine` · ROADMAP Phase 1

**Abnahme:** Workflow nach Kill mid-run mit gleicher `thread_id` resumierbar.

---

## P8 — Agent-Contract erzwingen

**Intent:** Agent = Vertragspartner der Platform, kein freies Skript.

**Regeln**
- Jeder Agent erbt/implementiert SDK (`agent_base.py`).
- **Input** und **Output** = typisierte DataProducts (Pydantic).
- Tools nur über MCP-Adapter (P5).
- `tenant_id` immer explizit — nie global implizit.
- Instantiierung scheitert, wenn Contract verletzt.

**Verboten:** Agent schreibt direkt in Postgres/Qdrant/Letta; „halb-SDK“-Agenten in Prod.

**Wo:** [02-AGENT-SDK.md](02-AGENT-SDK.md) · Contract-Tests Phase 3

**Abnahme:** `tests/contract/` rot, wenn Agent DP/MCP umgeht.

---

## P9 — Alles in die Datenbank

**Intent:** Was in der VM entsteht oder geholt wird, ist **nachvollziehbar persistiert**.

**Regeln**
- Pflicht am Run-/Workflow-Ende: mindestens **A** (Audit); fachlich relevante Outputs zusätzlich als DP → **G** und/oder K/L1/L2/L3/SK laut Schema.
- Working-/Tactical-Memory am Ende **destillieren oder verwerfen mit Audit** — nie still verschwinden.
- Gilt auch für Capture-Imports (P19).

**Verboten:** „Ergebnis nur in Console-Response“; wichtige Fakten nur im LLM-Kontext behalten.

**Wo:** DP-Commit · Pipeline-Agent · Memory-Curators

**Abnahme:** Nach Test-Workflow: Eintrag in `ai_os_log` + erwartetes DP/KG; Gate-Check in Platform-Gate.

---

## P10 — Platform vor Fach-Agenten

**Intent:** Verkaufbare Fach-SKUs stehen auf einer **grünen Platform**, nicht auf Sand.

**Regeln**
- Reihenfolge: Infra → Core (+ Memory Gateway) → Platform-Agenten → **Platform-Gate** → Fach-SKUs.
- Gate umfasst u. a. Persistenz, Search, MCP, Scheduler, Memory-Curator, Company-Brain-Mindestgates (siehe ROADMAP).

**Verboten:** Research/Blog-Deploy „zum Ausprobieren“ vor Gate; Gate überspringen in Prod-Profilen.

**Wo:** ROADMAP Phase 2 · `tests/platform_gate`

**Abnahme:** `python -m tests.platform_gate --tenant …` exit 0 vor erstem `deploy/agents/*.yml`.

---

## P11 — Unified Search + Memory Gateway

**Intent:** Eine Such-API und eine Inference-Tür für die ganze Platform.

**Regeln**
- **Unified Search:** ein Endpoint fusioniert L1 + G + SK + A (Query-Router wählt Schichten — nicht blind alles).
- **Memory Gateway:** jedes LLM über diese Tür; Persist-Hook + LangFuse Pflicht (P12/P17/P19).
- Fach-Agenten implementieren **keine** eigene Suche/kein eigenes Modell-Routing.

**Verboten:** Agent → OpenRouter direkt; Agent → eigener Qdrant-Client für „meine“ Suche.

**Wo:** `search-service` · Memory Gateway · [11-PLATFORM-VM.md](11-PLATFORM-VM.md)

**Abnahme:** `POST /v1/search` liefert gemischte Quellen; Cloud-Call ohne Gateway in PROD unmöglich.

---

## P12 — FinOps by Design

**Intent:** Kosten sind Produktfeature, nicht Überraschung.

**Regeln**
- Default-Modus **`sovereign`** (Ollama LAN/lokal).
- Cloud (`balanced`/`premium`) nur bei explizitem Modus oder klarer Policy-Eskalation.
- Zielkorridor: **≥ 80 %** Calls lokal (Messung über Zeitfenster/Tenant).
- Jeder Cloud-Call: LangFuse-Tag + Audit + später Run-Receipt (Kosten micro-USD).

**Verboten:** Stiller Default auf teures Cloud-Modell; Keys in Frontend.

**Wo:** `config/compute.yaml` · LangFuse · Run-Receipts (P17)

**Abnahme:** Dashboard/Query zeigt Anteil lokal vs. cloud; Eskalation hat Audit-Grund.

---

## P13 — Qualität durch Kontext, nicht durch teureres Modell

**Intent:** Wenn die Antwort schlecht ist, zuerst Bundle/Retrieval/Skills verbessern.

**Regeln**
- Vor Premium-Eskalation: Context Bundle prüfen, Search nachschärfen, Skill laden, Guardrails.
- Premium nur wenn: Nutzer wählt `premium` **oder** Policy nach fehlgeschlagenem Qualitätscheck (P16) es erlaubt.

**Verboten:** „Einfach Claude, dann wird’s besser“ als Standard-Reaktionsmuster im Code.

**Wo:** Model-/Memory-Gateway Auto-Router · Observer (P16)

**Abnahme:** Eskalations-Log zeigt vorherigen Kontext-/Observer-Schritt, nicht nur Modellwechsel.

---

## P14 — Skalierung ohne Architekturwechsel

**Intent:** Vom Tuxedo-DEV bis Air-Gap-Enterprise derselbe Stack.

**Regeln**
- Gleiche Compose-Schichten (`infra`, `monitoring`, `core`, `platform-agents`, `agents/*`).
- Unterschied nur: Hardware, aktive SKUs, Inference-Ort (remote Ollama vs. lokal), Lizenz.

**Verboten:** „Für Enterprise schreiben wir Kubernetes-only-Fork“; anderer DB-Stack pro Tier.

**Wo:** [04-DEPLOYMENT.md](04-DEPLOYMENT.md) · [06-PRODUKT-DEPLOYMENT.md](06-PRODUKT-DEPLOYMENT.md) · ROADMAP §19

**Abnahme:** Gleiches `docker compose …` Schema auf Dev- und Starter-VM dokumentiert und getestet.

---

## P15 — PGE-Trinity (Planner → Gatekeeper → Executor)

**Intent:** Das LLM plant; **Code** entscheidet, ob ein Tool-Call erlaubt ist; erst dann Ausführung.

**Regeln**
- **Planner (LLM):** schlägt Schritte/Tool-Calls vor.
- **Gatekeeper (Code):** prüft Risk-Klasse GREEN/YELLOW/ORANGE/RED, Policies, PII, Caps, License.
- **Executor:** sandboxed / nur freigegebene MCP-Tools.
- YELLOW+ kann Human-in-the-Loop erfordern (Config).

**Verboten:** Agent führt Tool-Calls aus, bevor Gatekeeper gelaufen ist; Gatekeeper als LLM-Prompt.

**Wo:** Guardrails-Agent / SDK-Hooks · Cognithor-Vorbild in ROADMAP

**Abnahme:** RED-Tool wird blockiert (Test); Audit enthält Gatekeeper-Decision.

---

## P16 — Observer Audit Layer

**Intent:** Antwortqualität wird lokal und billig gegengeprüft.

**Regeln**
- Nach Agent-Antwort: deterministischer Trigger → Check mit **lokalem** Modell.
- Prüfaspekte mind.: Halluzination, Sycophancy, Faulheit, Tool-Ignoranz (laut Roadmap).
- Bei Verstoß: Regeneration oder Re-Loop; **fails open** (System bleibt nutzbar, Verstoß wird geloggt).

**Verboten:** Observer blockiert Prod hart ohne Fallback; Observer nur in Cloud.

**Wo:** Platform-Agent / Post-Hook Phase 2

**Abnahme:** Injizierter „fauler“ Stub → Observer-Flag in Audit + mind. ein Retry.

---

## P17 — Manipulationssicheres Audit

**Intent:** Runs sind belegbar — für Compliance und FinOps.

**Regeln**
- `ai_os_log`: jeder Eintrag `prev_hash` + `entry_hash` (SHA-256 über kanonisches JSON).
- Pro Workflow-Run: **Run-Receipt** (Kosten, Modelle, Scopes, Cloud-Eskalationen, Chain-Hash, Signatur).
- Verifikation: `chain_verify(tenant_id)` ohne Lücke.

**Verboten:** Audit-Update in-place ohne neue Kette; Receipt ohne Signatur in Prod.

**Wo:** Schema Phase 0 · Audit-Service

**Abnahme:** Manipulierter Log-Eintrag bricht `chain_verify`; Receipt zu Test-Run vorhanden.

---

## P18 — Company Brain vor Second Brain

**Intent:** Die Firma hat **eine** Wahrheitsschicht — nicht 12 persönliche Notizgraphen.

**Regeln**
- **SSOT** = K + G (+ kuratiertes L1). Detail: [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md).
- Letta = Agent-Runtime-Gedächtnis (Episoden/Profil), Quelle für Destillation — **nicht** SSOT.
- Writes: nur DataProduct → DP-Commit; Reads: MCP `kg`/`memory` + Unified Search.
- Roh-Chat / Capture → L2 möglich; **`org:Claim` / Decisions** nur über Curator + Gate.

**Verboten:** „Obsidian ist das Company Brain“; Agent `INSERT` in `kg_*`; Letta = alleinige Wahrheit.

**Wo:** P18-Spec · GATE-CB-* · org-brain Schema

**Abnahme:** Company-Brain-Abnahmefragen (ROADMAP §12.4.5) bestanden; kein GraphRAG-Marketing vor Gate.

---

## P19 — Platform-VM first — eine Tür, ein Gedächtnis

**Intent:** Das erste verkaufbare Produkt ist die **Appliance**, nicht ein einzelner Fachagent.

**Regeln**
- Lizenzprodukt #1 = **Platform-VM + `AIOS-CORE`** — [11-PLATFORM-VM.md](11-PLATFORM-VM.md).
- **Isolation:** eine Welt = eine VM = ein Company Brain (NCE-Werkstatt physisch getrennt von jeder Kunden-VM).
- **NCE First-Party:** Company Brain wird auf der DEV-VM **selbst genutzt** (Entwicklung + eigenes Org-Wissen).
- **DEV-VM:** Cursor + Antigravity **in** der VM; Host nur KVM.
- **PROD-VM:** kein Dev-Tooling; Kunde nur Browser; nur Kunden-Brain.
- **Memory Gateway:** alle LLM-Calls; Persist-Hook Pflicht **in dieser VM**.
- **Chat Capture:** Gemini, Antigravity, ChatGPT-Export → gleicher Normalizer → Speicher **dieser** VM.
- Kein Auto-Sync DEV → Kunden-Image (nur bewusste Seeds/SKU-Doku).
- Policy „eine Tür“: PROD kein direkter Public-LLM-Outbound.

**Verboten**
- Paralleles „Neben-Gedächtnis“ (Chats nur in Gemini-History).
- Shared DB/Volumes zwischen NCE-DEV und Kunden-PROD.
- Cursor/Antigravity-Pflicht auf dem Host mit Sync-Poller wie v1.
- Fach-SKU als erstes Produkt ohne Core-VM.

**Wo:** Phase 0 / 1 / 1b · docs/11 · deploy/chat-capture.yml

**Abnahme:** Gemini- oder Antigravity-Chat von gestern über Unified Search auffindbar; Health der Core-VM ohne Fachagent grün.

---

## Wie man die Prinzipien im Alltag prüft

1. **Design-Review:** „Welches P wird hier verletzt?“ — wenn keins greift, Feature ist Scope-creep oder fehlt ein P.
2. **CI:** Contract-Tests (P8), Arch-Lint gegen Direkt-HTTP (P5), Gate vor Agents (P10).
3. **Betrieb:** LangFuse + chain_verify + Search-Stichproben (P11/P12/P17/P19).

Änderungen an Prinzipien nur per **ADR** in `docs/adr/` + Update dieser Datei und ROADMAP-Kurzform.
