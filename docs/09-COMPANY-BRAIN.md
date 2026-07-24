# AI-OS v2 — Company Brain (Wissensmanagement)

**Stand:** Juli 2026 · **Operativ:** [ROADMAP.md §12.4](../ROADMAP.md#124-company-brain--wissensmanagement)  
**Einfach erklärt:** [10-MEMORY-EINFACH.md](10-MEMORY-EINFACH.md)  
**Verwandt:** [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) · [03-DATENPRODUKTE.md](03-DATENPRODUKTE.md) · [02-AGENT-SDK.md](02-AGENT-SDK.md)  
**Impuls:** Leonard Schmedding — [„Wieso KI Second Brains scheitern“](https://www.youtube.com/watch?v=81pDusm5nZE) (Company Brain als SSOT)

---

## 1. Einordnung

### 1.1 Was Company Brain ist — und was nicht

| Ist | Ist nicht |
|-----|-----------|
| **Single Source of Truth** für Mandantenwissen (K + G + kuratiertes L1) | Persönlicher Obsidian-/Notion-„Second Brain“ |
| Abfragbare Ontologie für Mensch, Agent, Dashboard, App | Schöner Visual-Graph ohne Betriebsfragen |
| Persistenz über **Datenprodukte + DP-Commit** | Agent schreibt frei in Dateien/Qdrant/Letta |
| Zugriff nur über **Orchestrator / Unified Search / MCP `kg` + `memory`** | Direkte DB-Zugriffe aus Fach-Agenten |
| Reduktion + Curators (P2) | Data Lake „alles indexieren“ |
| **Pro Platform-VM eine Brain-Welt** (NCE-Werkstatt ≠ Kunden-PROD) | Geteilte Cloud-DB zwischen Entwickler und Kunde |

**First-Party:** NCE nutzt Company Brain auf der **eigenen DEV-/Werkstatt-VM** (Cursor/Antigravity + Capture → dieses Brain). Kunden jeweils auf **eigener PROD-VM**. Siehe [11-PLATFORM-VM.md § Isolationsmodell](11-PLATFORM-VM.md#isolationsmodell-verbindlich-eine-welt--eine-vm--ein-company-brain).

### 1.2 Abgrenzung der Speicherrollen (verbindlich)

```
Company Brain (SSOT)
  K  kanonische Dateien / registry
  G  Knowledge Graph (org:* + platform:* + Fach-SKU-Typen)
  L1 kuratierte Embeddings (nur published / freigegeben)

Agent Runtime Memory (nicht SSOT)
  Working / Tactical   flüchtig pro Run
  L2 Letta Archival    episodisch („was passierte letzte Woche?“)
  L3 Letta Core        User-Modell / Profil-Fakten

Verdichtung (nur über Platform-Agenten + DP-Commit)
  L2-Curator → Archival
  L3-Curator → org:Claim (+ Kante) in G   ← nie „Roh-Chat = Decision“
  Skill-Distiller → SK
```

**Regel:** Letta ist das Gedächtnis des Agenten. Company Brain ist das Gedächtnis der Firma.  
L3-Curator **darf** Claims in G schreiben — nur als typisiertes DataProduct über `POST /v1/dataproduct/commit`, nicht als freier Letta→Postgres-Sidechannel.

### 1.3 Unverhandelbare Plattform-Vorgaben

Company Brain verletzt **keine** Leitprinzipien:

| Prinzip | Anwendung im Company Brain |
|---------|----------------------------|
| **P2** | Roh-Chat, Working-Memory, Entwürfe → nicht L1; Decisions nur nach Destillation/Gate |
| **P3** | Beziehungen (Decision→Meeting→Offering) in G, nicht nur Vektor-Ähnlichkeit |
| **P4** | Speicherziel + Edge-Mapping = Code im DP-Service / Schema-Registry |
| **P5** | Agenten: externe Welt nur via MCP; KG-Lesen via MCP `kg` / Platform Search |
| **P8** | Input/Output = DataProduct; Tools nur `self.mcp` |
| **P9** | Jeder Brain-Write: G + A (+ ggf. K/L1); kein „nur im Prompt behalten“ |
| **P10** | `org-brain`-SKU und Brain-Seed erst nach Platform-Gate (Phase 2 grün) |
| **P11** | Kein Fach-Agent baut eigene Suche — Unified Search fusioniert L1+G+SK+A |
| **P15** | `kg.upsert_*` und Decision-Writes: Risk-Klasse ≥ YELLOW, Gatekeeper prüft |

---

## 2. Architektur-Pfad (kein Bypass)

```
Fach-Agent / Platform-Agent
    │  nur self.mcp.*  und  ContextBundle
    ▼
MCP-Gateway (Allowlist + Caps + Audit → A)
    │  kg.search | kg.traverse | kg.resolve
    │  memory.search_archival | …
    │  search (Unified Search Platform-Service)
    ▼
Orchestrator DP-Service
    │  POST /v1/dataproduct/commit
    │  schema validate (L0) → storage_target deterministisch
    ▼
G (kg_nodes/kg_edges) + A (+ K / L1 laut Schema)
```

**Verboten:**
- Agent öffnet Postgres/`kg_*` direkt
- Agent upsertet Qdrant ohne Ingest-Agent / DP-Flag `ingest_recommended`
- Agent schreibt Letta Archival und behandelt das als kanonische Firmenwahrheit
- Console speichert Decisions nur im Browser-LocalStorage

**Erlaubt:**
- Orchestrator baut DomainSlice aus `kg.traverse` (Platform-Code)
- Memory-Agent (Platform) destilliert L2→L3→`org:Claim` DP
- Ingest-Agent materialisiert `org:KnowledgeAsset` aus K

---

## 3. L0-Schema — Mindest-Ontologie `org:*`

Erweitert die Platform-Ontologie; ersetzt sie nicht.  
Blog (`blog:*`) und Email (`email:*`) bleiben in ihren SKU-Paketen.

### 3.1 Entity-Typen (10)

| ID | Key | Pflichtfelder | Primäre DP-Klasse | Ingest / Erzeuger |
|----|-----|---------------|-------------------|-------------------|
| `org:Person` | `person_id` | name, role?, email? | `OrgPerson` | Seed / Mail-From / manuell |
| `org:Organization` | `org_id` | name, kind (customer\|partner\|university\|internal) | `OrgOrganization` | Seed / Mail-Domain |
| `org:Offering` | `offering_id` | name, kind (training\|consulting\|product) | `OrgOffering` | Seed (Portfolio) |
| `org:Engagement` | `engagement_id` | title, status, org_id? | `OrgEngagement` | Briefing / Angebot |
| `org:Meeting` | `meeting_id` | title, held_at, source_ref? | `OrgMeeting` | Calendar-MCP → time-agent DP |
| `org:Decision` | `decision_id` | title, status, decided_at, summary | `OrgDecision` | Meeting-Follow-up / Human-Gate |
| `org:Policy` | `policy_id` | title, scope | `OrgPolicy` | `knowledge/` + Compliance |
| `org:KnowledgeAsset` | `asset_id` | path (K), title, kind | `OrgKnowledgeAsset` | Ingest / Publish |
| `org:Claim` | `claim_id` | text, confidence (0..1), valid_from? | `OrgClaim` | L3-Curator / Research |
| `org:Skill` | `skill_id` | → alias auf `platform:Skill` in v2 | `SkillCreated` | Skill-Distiller |

**Status-Enums (deterministisch im Schema, nicht LLM):**
- `org:Decision.status`: `proposed` \| `active` \| `superseded`
- `org:Engagement.status`: `pipeline` \| `active` \| `closed`
- `org:Claim`: nur `confidence >= 0.7` default in GraphRAG-Retrieval (Config)

### 3.2 Edge-Typen (8 + Platform)

| ID | from → to | Bedeutung |
|----|-----------|-----------|
| `attended_by` | Meeting → Person | Teilnehmer |
| `about` | Meeting\|Decision → Offering\|Engagement\|Organization | Thema |
| `decided_in` | Decision → Meeting | Provenance |
| `supersedes` | Decision\|Policy\|Skill → gleicher Typ | Gültigkeit |
| `applies_to` | Policy → Offering\|Engagement\|Tenant | Scope |
| `documents` | KnowledgeAsset → Decision\|Meeting\|Offering\|Policy | Kanonische Quelle in K |
| `asserts` | KnowledgeAsset\|AgentRun → Claim | Fakt-Herkunft |
| `supports` | Claim → BlogPublished\|Offering\|Engagement\|Decision | Belegkette |

Platform-Kanten bleiben Pflicht: `belongs_to_tenant`, `derived_from`, `governed_by`, `produced_by` (DP→AgentRun).

### 3.3 Dateiorte (Repo)

```
config/kg-platform-schema.yaml          # unverändert Kern
packages/org-brain/schema/entities.yaml # NEU — org:* Entities
packages/org-brain/schema/edges.yaml    # NEU — org:* Edges
customers/nextchapter/knowledge/seed/   # Seed-Markdown → Ingest → DPs
customers/nextchapter/schema/overrides.yaml  # optional Tenant-Erweiterungen
```

SKU `org-brain` ist ein **Platform-naher Fach-Seed-Paket**, kein Agent mit eigener Inference-Pipeline.  
Aktivierung: Tenant `active_packages` enthält `org-brain` **nach** Platform-Gate.

---

## 4. Datenprodukte (Catalog-Auszug)

Alle Brain-Writes sind DataProducts. `storage_target` ist **im Schema fix**, nicht vom LLM wählbar.

| DP-Klasse | produced_by (typisch) | storage_target | ingest_recommended |
|-----------|----------------------|----------------|--------------------|
| `OrgOffering` | `console` / seed-job | `["G","K"]` | false |
| `OrgPolicy` | `guardrails-agent` / seed | `["G","K"]` | false |
| `OrgMeeting` | `time-agent` | `["G"]` | false |
| `OrgDecision` | `research-agent` oder `console` (+ Human-Gate) | `["G","K"]` | false |
| `OrgKnowledgeAsset` | `ingest-agent` | `["G","K"]` | true nur wenn published |
| `OrgClaim` | `memory-agent` (L3-Curator) | `["G"]` | false |
| `OrgEngagement` | `console` / fachlicher Workflow | `["G","K"]` | false |
| `OrgPerson` / `OrgOrganization` | seed / email-agent enrich | `["G"]` | false |

Vollständige Pydantic-Definitionen: [03-DATENPRODUKTE.md § Company-Brain-Produkte](03-DATENPRODUKTE.md#company-brain-produkte).

### 4.1 Commit → Graph-Mapping (deterministisch)

```
DP-Commit(OrgDecision)
  → kg_nodes upsert org:Decision
  → edges: belongs_to_tenant, decided_in?, about?, supersedes?, produced_by(AgentRun)
  → optional K: customers/{tenant}/knowledge/decisions/{decision_id}.md
  → A: audit row + hash-chain (P17)
```

Kein Agent ruft `kg.upsert_node` für Decisions außerhalb des DP-Services.  
MCP-Tool `kg.upsert_node` ist **nur** dem Orchestrator/DP-Service und Memory-Agent (Platform) erlaubt — Caps in `mcp-servers.yaml`.

---

## 5. MCP-Oberfläche

### 5.1 Native Server `kg` (erweitert)

| Tool | Wer darf | Zweck |
|------|----------|-------|
| `search` | alle Agenten (Tenant-scoped) | Entity-Suche |
| `traverse` | alle Agenten | hops≤2 (Config) |
| `resolve` | alle Agenten | DP-ID / entity key → Node+Edges |
| `upsert_node` | **nur** platform roles (dp-service, memory-agent) | Cap niedrig |
| `upsert_edge` | **nur** platform roles | Cap niedrig |

Fach-Agenten **lesen** Graph über MCP; **schreiben** indirekt über Output-DP → Commit.

### 5.2 Unified Search (P11) + Query-Router

`POST /v1/search` und Context-Building laufen **nicht** blind über alle Schichten.  
Zuerst entscheidet der **deterministische Query-Router** (siehe [§12](#12-betriebsoptimierungen-verbindlich)), welche Schichten überhaupt befragt werden. Danach ggf. Score-Fusion — Platform-Code, kein Fach-Agent.

### 5.3 Memory MCP

| Tool | Nutzung im Brain-Kontext |
|------|--------------------------|
| `search_archival` | EpisodicSlice — „was besprachen wir?“ |
| `add_archival` | nur Memory-Agent / Orchestrator-Hook nach Run |

Archival-Treffer werden **nicht** als `org:Decision` ausgegeben, bevor L3-Curator ein `OrgClaim`/`OrgDecision`-DP erzeugt hat.

---

## 6. Context Bundle — DomainSlice

```python
# Orchestrator — deterministisch
def build_domain_slice(intent: str, tenant_id: str) -> DomainSlice:
    entities = intent_entity_hints(intent)  # Regel/NER, kein freies LLM-Routing
    nodes = []
    for e in entities:
        nodes.extend(mcp_kg.traverse(e, tenant_id, hops=2,
                      type_filter=["org:*", "blog:*", "platform:*"]))
    return DomainSlice(nodes=nodes, edges=collect_edges(nodes))
```

GraphRAG (Phase 6) erweitert RetrievalSlice; DomainSlice existiert ab Phase 2 sobald `org-brain` Schema geladen ist.

---

## 7. Seed Next Chapter (M1)

Mindestinhalt nach Aktivierung von `org-brain` für Tenant `nextchapter`:

| Typ | Seed-Objekte |
|-----|----------------|
| `org:Offering` | Training & Workshops · Consulting (PBD) · AI-OS |
| `org:Policy` | Blog-Disclaimer 2026-06 · DSGVO Lernplattform · No-Tool-Sales Consulting |
| `org:KnowledgeAsset` | Portfolio-Strategie, SA-Master, ausgewählte Blog-Published-Pfade |
| `org:Organization` | PBD Experts · UTM · SAP Community Launchpad (referenziell) |
| `org:Person` | Peter Alexander (Operator) |

DoD Seed: `GET /v1/kg/stats?tenant=nextchapter` zeigt **≥ 10 Nodes** mit Prefix `org:` und **≥ 5 Edges** außerhalb `belongs_to_tenant`.

---

## 8. Abnahmefragen (Company-Brain-Gate)

Diese Fragen müssen **ohne** reine Vektor-Rate beantwortbar sein (G-Traverse + optional L1):

1. Welche **active** Decisions betreffen Offering `consulting`?
2. Welches Meeting dokumentiert Decision X? (`decided_in`)
3. Welche Policy gilt für LinkedIn-Teaser? (`applies_to` / `governed_by`)
4. Welche Claims stützen BlogPublished Y? (`supports`)
5. Welches KnowledgeAsset in **K** ist kanonisch für Offering `ai-os`? (`documents`)

Fail → kein GraphRAG-Marketing, kein „Company Brain“ in Produkttexten.

---

## 9. Build-Reihenfolge (einbettet in Phasen)

| Wann | Was | Gate |
|------|-----|------|
| Phase 0 | L0 YAML `org-brain` Schema im Repo | Schema-Lint |
| Phase 1 | Unified Search indexiert `org:*` sobald Nodes existieren | Search-Hook |
| Phase 2 | DP-Klassen + Commit-Mapping + MCP Caps; Memory L3→Claim | Platform-Gate + Brain-Subgate |
| Phase 2+ | Seed nextchapter | Stats-DoD |
| Phase 4 | time-agent → OrgMeeting; blog cites/supports | Fach-Agent-Tests |
| Phase 5 | Console `/platform/kg` filter `org:*`; Decision-Inbox (Human-Gate) | UI-Smoke |
| Phase 6 | GraphRAG nutzt `org:*` in RetrievalSlice | GraphRAG-DoD |

**Kein** Fach-Agent vor Platform-Gate (P10).  
**Kein** Massen-Ingest von Chats in `org:Decision`.

---

## 10. Anti-Patterns (explizit verboten)

1. Obsidian-Sync als Company Brain  
2. „Alles was Letta weiß, ist Firmenwahrheit“  
3. Fach-Agent mit eigenem Neo4j/NetworkX-Graph  
4. 50 Entity-Typen in Woche 1  
5. Visual-KG ohne die 5 Abnahmefragen  
6. Speichern von Entwürfen in L1 „weil praktisch“  
7. Alle Schichten bei jeder Query befragen (kein Query-Router)  
8. Graph-Knoten ohne kanonische Datei bei Typen, die K verlangen  
9. Claims ohne Provenance / ohne Dedup in G schreiben  

---

## 11. Bezug v1

v1 G0 (`kg-platform-schema.yaml`, blog/email schemas) bleibt Referenz und wird nach v2 portiert.  
Company Brain **ergänzt** um `org:*` — das fehlende Firmenhirn zwischen Content-Factory-Metadaten und Agent-Memory.

---

## 12. Betriebsoptimierungen (verbindlich)

Drei Maßnahmen gegen die häufigsten Schwächen (Doppel-Suche, Claim-Müll, K↔G-Drift).  
Umsetzung: Platform-Code in Phase 1–2 — **kein** Fach-Agent.

### 12.1 Query-Router (deterministisch)

**Problem:** L1 und Letta Archival sind beide „semantisch“. Ohne Router suchen Agents doppelt oder am falschen Ort.

**Regel:** Vor jedem `POST /v1/search` und vor dem Bau von RetrievalSlice / EpisodicSlice / DomainSlice:

```python
# core/orchestrator/query_router.py — Code, kein LLM (P4)
class SearchPlan(BaseModel):
    use_g: bool = False       # Knowledge Graph
    use_k_resolve: bool = False  # Datei nach Node-ID laden
    use_l1: bool = False      # Qdrant
    use_letta: bool = False   # Archival / Core
    use_sk: bool = False      # Skills
    use_a: bool = False       # Audit (Operator)
    max_l1: int = 5
    max_graph_nodes: int = 20
    hops: int = 2

INTENT_RULES = [
    # (intent_prefix oder keyword-set, plan)
    ({"decision", "gilt", "policy", "offering", "regel"}, 
     SearchPlan(use_g=True, use_k_resolve=True, use_l1=False, use_letta=False)),
    ({"ähnlich", "wie blog", "recherche", "quellen"}, 
     SearchPlan(use_l1=True, use_g=True, use_sk=True, max_l1=5)),
    ({"gestern", "letzte woche", "besprochen", "erinnerst"}, 
     SearchPlan(use_letta=True, use_g=False, use_l1=False)),
    ({"wie haben wir", "skill", "ablauf", "verfahren"}, 
     SearchPlan(use_sk=True, use_g=False, use_l1=True, max_l1=3)),
]

DEFAULT_PLAN = SearchPlan(use_g=True, use_l1=True, use_sk=True, max_l1=5)
# Letta nur wenn Episodic-Keywords — nie Default-Hot-Path
```

| Intent-Klasse | Primär | Sekundär | Nie im Hot Path |
|---------------|--------|----------|-----------------|
| Geltung / Policy / Offering / Decision | G (+ K resolve) | — | L1, Letta |
| Ähnlichkeit / Research / Blog-Inhalt | L1 | G, SK | Letta |
| Episode / „was sagten wir“ | Letta | — | L1 als Ersatz für Geltung |
| Verfahren / Skill | SK | L1 | — |
| Operator / Audit | A | G | — |

**DoD:** Contract-Test: Intent „Welche Decision gilt für consulting?“ → Plan ohne `use_l1` und ohne `use_letta`.

### 12.2 Claim-Pipeline härten

**Problem:** L3-Curator (LLM) ist der fehleranfälligste Schritt — Halluzination, Duplikate, falsche `supports`-Kanten.

**Pipeline (Memory-Agent, wöchentlich + on-demand):**

```
L2 Archival (7d)
  → LLM Fact-Extraktion (nur Vorschläge)
  → Filter: confidence >= CLAIM_MIN_CONFIDENCE (Default 0.7)
  → Dedup: Embedding-Ähnlichkeit gegen bestehende org:Claim (Cosine ≥ 0.95 → skip/merge)
  → Provenance Pflicht: asserts_from_ref = KnowledgeAsset-ID oder AgentRun-ID
  → Risk-Klasse:
       Claim nur textuell          → GREEN  → auto DP-Commit
       Claim + supports → Offering|Decision → YELLOW → Human-Gate (Console)
  → OrgClaim DataProduct → DP-Commit (nie Direkt-SQL)
```

| Regel | Wert |
|-------|------|
| `CLAIM_MIN_CONFIDENCE` | `0.7` (Config, Tenant überschreibbar) |
| Dedup-Schwelle | Cosine ≥ `0.95` gegen bestehende Claims desselben Tenants |
| `supports` auf Decision/Offering | immer Human-Gate |
| `valid_to` | optional; Default +365 Tage wenn gesetzt; Job `claim-stale` markiert abgelaufen |
| Max. neue Claims / Curator-Lauf | Cap `50` / Tenant |

**DoD:** Integrationstest — zwei semantisch gleiche Fact-Vorschläge → ein Claim; `supports` ohne Gate → Reject.

### 12.3 Atomarer Commit (K ↔ G)

**Problem:** Datei in K und Knoten in G laufen auseinander → „zwei Wahrheiten“.

**Regel:** Für DataProducts mit `storage_target` enthaltend **`G` und `K`** (u. a. `OrgDecision`, `OrgPolicy`, `OrgOffering`, `OrgEngagement`, `OrgKnowledgeAsset`):

1. Eine Transaktion / ein Commit-Request  
2. Reihenfolge im DP-Service (deterministisch):
   1. Schema validate  
   2. Datei nach K schreiben (Pfad aus Schema/Convention)  
   3. `kg_nodes` upsert  
   4. `kg_edges` upsert (inkl. `documents` → Asset-Pfad)  
   5. Audit (A) + hash-chain  
3. Bei Fehler in Schritt 3–4: **Rollback** der Datei (oder Status `commit_failed`, Node nicht „active“)  
4. Kein „Graph zuerst, Datei irgendwann“ und kein „Datei ohne Node“ für diese Typen  

```python
# Pseudocode DP-Service
async def commit_canonical(dp: DataProduct) -> CommitResult:
    assert "G" in dp.storage_target and "K" in dp.storage_target
    async with unit_of_work() as uow:
        path = write_canonical_file(dp)          # K
        node_id = upsert_kg_node(dp, path=path)  # G
        upsert_kg_edges(dp, node_id)             # G
        audit_append(dp, node_id, path)          # A
        uow.commit()  # alles oder nichts
```

**Ausnahmen (bewusst):**
- `OrgMeeting`, `OrgClaim`, `OrgPerson` — oft nur `G` (kein K-Zwang)
- `BlogDraft` — K+G, aber `ingest_recommended=false` (kein L1)

**DoD:** Test — Commit bricht bei Edge-Fehler ab → keine verwaiste Decision-Datei ohne Node; Reverse: kein active Decision-Node ohne lesbare K-Datei.
