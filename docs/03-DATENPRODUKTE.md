# AI-OS v2 — Datenprodukte: Schema-Catalog & Datenflusskarte

**Stand:** Juli 2026 (Company-Brain-Produkte 2026-07-22) · **Verwandt:** [02-AGENT-SDK.md](02-AGENT-SDK.md) · [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) · [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md)

---

## Warum Datenprodukte?

In v1 produzierten Agenten Outputs als:
- Roh-Dictionaries in Postgres-Tabellen
- Markdown-Dateien auf dem Dateisystem
- Direkte Qdrant-Upserts
- Return-Werte die niemand speicherte

In v2 gibt es **einen einzigen Datenpfad**: jeder Agent-Output ist ein typisiertes DataProduct das über `POST /v1/dataproduct/commit` in die Plattform-Schichten geschrieben wird.

**Ergebnis:**
- Jeder Output ist in G (Knowledge Graph) als Knoten nachverfolgbar
- Jeder Output hat Provenienz (welcher Agent, welcher Workflow, welcher Tenant)
- Observability: Console kann jeden Datenfluss als DP-Stream anzeigen
- Composability: Agent A's Output ist Agent B's Input — per DP-ID referenziert

---

## Basis-Schema (DataProduct)

```python
class DataProduct(BaseModel):
    dp_id: str              # UUID, auto-generiert
    schema_version: str     # "1.0"
    tenant_id: str          # Pflicht — Tenant-Isolation
    produced_by: str        # Agent-ID oder "console" oder "scheduler"
    produced_at: datetime   # auto-gesetzt
    workflow_run_id: str | None  # Traceability

    # Speicher-Steuerung
    storage_target: list[str]   # ["G"] oder ["G","L1"] oder ["G","K"]
    ingest_recommended: bool     # True → Ingest-Worker indexiert in L1
```

---

## Schema-Catalog

### Plattform-Produkte

```python
class DailyBriefing(DataProduct):
    """Tages-Briefing — täglich vom Scheduler produziert."""
    produced_by = "research-agent"
    storage_target = ["G", "L2"]      # Graph + Episodisches Gedächtnis

    date: date
    email_summary: str
    calendar_summary: str
    highlights: list[str]
    action_items: list[str]
    full_text: str

class AgentRunRecord(DataProduct):
    """Audit-Record für jeden Agenten-Lauf."""
    produced_by: str                   # Agent-ID
    storage_target = ["G", "A"]       # Graph + Audit (unveränderlich)

    intent: str
    status: Literal["success", "failure", "interrupted"]
    duration_seconds: float
    token_count: int
    steps_completed: list[str]
    error_message: str | None

class SkillCreated(DataProduct):
    """Neues Skill-Dokument wurde destilliert."""
    produced_by: str
    storage_target = ["G", "SK"]

    skill_id: str
    skill_title: str
    skill_version: int
    trigger_run_id: str              # Welcher AgentRun hat ihn ausgelöst?
```

### Research-Produkte

```python
class ResearchSession(DataProduct):
    """Recherche-Ergebnis."""
    produced_by = "research-agent"
    storage_target = ["G", "L1"]
    ingest_recommended = True

    query: str
    summary: str
    key_findings: list[str]
    sources: list[Source]
    confidence: float = Field(ge=0.0, le=1.0)
    depth: Literal["quick", "deep"]

class Source(BaseModel):
    url: str
    title: str
    relevance: float
    excerpt: str | None

class ResearchBrief(DataProduct):
    """Kurzform der ResearchSession für Downstream-Agenten."""
    produced_by = "research-agent"
    storage_target = ["G"]

    query: str
    brief: str                       # 200-Wort-Zusammenfassung
    source_session_id: str           # DP-ID der ResearchSession
```

### Blog-Produkte

```python
class BlogDraft(DataProduct):
    """Blog-Entwurf — noch nicht freigegeben."""
    produced_by = "blog-agent"
    storage_target = ["G", "K"]     # Graph + Dateisystem (pipeline/)
    ingest_recommended = False       # Erst nach Compliance-Freigabe

    title: str
    body: str
    teaser: str | None
    format: Literal["blog", "linkedin", "newsletter"]
    word_count: int
    research_ref: str               # DP-ID der ResearchSession
    compliance_status: Literal["pending", "cleared", "blocked"] = "pending"

class ComplianceReport(DataProduct):
    """Ergebnis des Compliance-Checks."""
    produced_by = "guardrails-agent"
    storage_target = ["G"]

    subject_dp_id: str              # Welches DP wurde geprüft?
    verdict: Literal["cleared", "blocked"]
    issues: list[ComplianceIssue]
    pii_findings: list[PIIFinding]
    brand_issues: list[str]

class ComplianceIssue(BaseModel):
    type: str
    severity: Literal["warn", "block"]
    message: str
    location: str | None

class BlogPublished(DataProduct):
    """Veröffentlichter Blog-Artikel."""
    produced_by = "blog-agent"
    storage_target = ["G", "K", "L1"]
    ingest_recommended = True       # → Qdrant-Indexierung

    title: str
    url: str
    published_at: datetime
    draft_ref: str                  # DP-ID des BlogDraft
    channel: str                    # "cms", "linkedin", "newsletter"
```

### Email-Produkte

```python
class EmailBatch(DataProduct):
    """Batch von E-Mails — Ergebnis des Mail-MCP-Calls."""
    produced_by = "email-agent"
    storage_target = ["G"]

    fetched_at: datetime
    count: int
    emails: list[EmailItem]
    has_invoices: bool
    has_action_items: bool

class EmailItem(BaseModel):
    message_id: str
    subject: str
    sender: str
    received_at: datetime
    is_invoice: bool
    invoice_ref: str | None

class Invoice(DataProduct):
    """Extrahierte Rechnung aus E-Mail."""
    produced_by = "email-agent"
    storage_target = ["G"]

    supplier: str
    amount: float
    currency: str = "EUR"
    date: date
    invoice_number: str | None
    category: str | None            # "hosting", "software", "office"
    email_ref: str                  # Message-ID

class TaxExport(DataProduct):
    """Steuer-Export für ein Jahr."""
    produced_by = "email-agent"
    storage_target = ["G", "K"]    # Graph + Dateisystem (exports/)

    tax_year: int
    invoices: list[Invoice]
    total_amount: float
    by_supplier: dict[str, float]
    export_path: str                # Pfad der exportierten CSV/JSON-Datei
    pii_cleared: bool = False       # Muss True sein vor Speicherung
```

### Kalender-Produkte

```python
class DaySchedule(DataProduct):
    """Tages-Kalender — Ergebnis des Calendar-MCP-Calls."""
    produced_by = "time-agent"
    storage_target = ["G"]

    date: date
    events: list[CalendarEvent]
    free_slots: list[TimeSlot]
    focus_time_hours: float

class CalendarEvent(BaseModel):
    title: str
    start: datetime
    end: datetime
    participants: list[str]
    location: str | None
    is_external: bool

class WeeklyPlan(DataProduct):
    """Wochenplan — automatisch erstellt."""
    produced_by = "time-agent"
    storage_target = ["G", "L2"]

    week_start: date
    priorities: list[str]
    scheduled_blocks: list[dict]
    unscheduled_items: list[str]
```

### Company-Brain-Produkte

> Spec: [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md) · ROADMAP §12.4 · Prinzip **P18**  
> Writes nur über diesen Catalog → `POST /v1/dataproduct/commit`. Kein `kg.upsert_*` aus Fach-Agenten.

```python
class OrgOffering(DataProduct):
    """Verkaufbares Angebot (Training / Consulting / Produkt)."""
    storage_target = ["G", "K"]
    ingest_recommended = False

    offering_id: str
    name: str
    kind: Literal["training", "consulting", "product"]
    summary: str | None = None

class OrgOrganization(DataProduct):
    storage_target = ["G"]
    org_id: str
    name: str
    kind: Literal["customer", "partner", "university", "internal"]

class OrgPerson(DataProduct):
    storage_target = ["G"]
    person_id: str
    name: str
    role: str | None = None
    email: str | None = None

class OrgEngagement(DataProduct):
    storage_target = ["G", "K"]
    engagement_id: str
    title: str
    status: Literal["pipeline", "active", "closed"]
    org_ref: str | None = None          # org_id
    offering_ref: str | None = None

class OrgMeeting(DataProduct):
    """Kalender-/Notiz-Meeting — typisch von time-agent nach Calendar-MCP."""
    produced_by = "time-agent"
    storage_target = ["G"]

    meeting_id: str
    title: str
    held_at: datetime
    attendee_refs: list[str] = []       # person_ids
    source_ref: str | None = None       # calendar event id oder K-path
    about_refs: list[str] = []          # offering/engagement/org keys

class OrgDecision(DataProduct):
    """Firmenentscheidung — Statuswechsel nach active nur mit Human-Gate."""
    storage_target = ["G", "K"]
    ingest_recommended = False

    decision_id: str
    title: str
    status: Literal["proposed", "active", "superseded"]
    decided_at: date | None = None
    summary: str
    meeting_ref: str | None = None
    about_refs: list[str] = []
    supersedes_ref: str | None = None

class OrgPolicy(DataProduct):
    storage_target = ["G", "K"]
    policy_id: str
    title: str
    scope: str
    applies_to_refs: list[str] = []

class OrgKnowledgeAsset(DataProduct):
    """Kanonisches Dokument in K — Brücke zu blog:/platform: Ingest."""
    produced_by = "ingest-agent"
    storage_target = ["G", "K"]
    # ingest_recommended nur wenn Asset published/freigegeben
    ingest_recommended: bool = False

    asset_id: str
    title: str
    path: str                           # relativ zu content/
    kind: str
    documents_refs: list[str] = []      # decision/meeting/offering/policy keys

class OrgClaim(DataProduct):
    """Stabiler Fakt aus L3-Curator — nie Roh-Chat."""
    produced_by = "memory-agent"
    storage_target = ["G"]

    claim_id: str
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    valid_from: date | None = None
    valid_to: date | None = None
    asserts_from_ref: str | None = None  # KnowledgeAsset oder AgentRun
    supports_refs: list[str] = []        # blog/offering/engagement/decision
```

**Commit-Mapping (deterministisch im DP-Service):**  
`OrgDecision` → Node `org:Decision` + Edges `belongs_to_tenant`, optional `decided_in`, `about`, `supersedes`, `produced_by`.  
Analog für die übrigen Klassen — siehe 09-COMPANY-BRAIN §4.1.

**Atomarer Commit (P18):** Typen mit `storage_target` ⊆ `{G,K}` (Decision, Policy, Offering, Engagement, KnowledgeAsset): Datei + Node + Edges + Audit in **einer** Unit-of-Work — siehe [09-COMPANY-BRAIN.md §12.3](09-COMPANY-BRAIN.md#123-atomarer-commit-k--g).

**OrgClaim-Härte:** `confidence≥0.7`, Dedup, Provenance Pflicht; `supports`→Offering/Decision nur mit Human-Gate — [§12.2](09-COMPANY-BRAIN.md#122-claim-pipeline-härten).

---

## Datenflusskarte

```
NUTZER-INPUT
    │
    ▼
Orchestrator: resolve_context()
    │
    ├──── SystemSlice    ← Tenant-Config, Policies
    ├──── DomainSlice    ← KG-Traversal
    ├──── TaskSlice      ← Input-DP-Refs, Params
    ├──── RetrievalSlice ← L1 Qdrant + GraphRAG
    ├──── EpisodicSlice  ← L2 Letta + letzte AgentRuns
    ├──── GuardrailSlice ← Compliance-Policies
    └──── SkillSlice     ← Relevante Skill-Dokumente
    │
    ▼
Workflow-Engine (LangGraph)
    │
    ├── Node 1: Agent.execute(InputDP)
    │       └── run() → produziert OutputDP
    │       └── dp_client.commit(OutputDP) → G + K + ggf. L1
    │
    ├── Node 2: Agent.execute(vorheriger OutputDP)
    │       └── ...
    │
    └── Node N: Letzter Output
            └── skill_hook.post_run() → ggf. Skill-Destillation
            └── AgentRunRecord.commit() → G + A
    │
    ▼
RESPONSE AN CONSOLE
    Output-DP-ID + Status
    (Console lädt DP on-demand via /v1/dataproduct/resolve)
```

---

## Speicher-Regeln nach storage_target

| Target | Speicher | Wann | Wer |
|--------|----------|------|-----|
| `G` | Postgres KG | immer | DP-Service (sync) |
| `K` | Dateisystem | wenn Schema `K` verlangt (z. B. OrgDecision, BlogDraft) — unabhängig von L1 | DP-Service / Ingest-Worker |
| `L1` | Qdrant | wenn `ingest_recommended: true` | Ingest-Worker (async) |
| `L2` | Letta Archival | täglich via L2-Curator | L2-Curator |
| `SK` | SQLite + Qdrant | nach Skill-Destillation | Skill-Service |
| `A` | Postgres ai_os_log | immer für AgentRunRecord | Orchestrator |

**Wichtig:** `G` ist immer Pflicht — kein DP ohne KG-Eintrag.

---

## DP-Commit API

```bash
# Commit eines DataProducts
POST /v1/dataproduct/commit
{
  "node_type": "blog:BlogDraft",
  "external_id": "dp-uuid-hier",
  "tenant_id": "nextchapter",
  "produced_by": "blog-agent",
  "workflow_run_id": "wf-uuid-hier",
  "payload": {
    "title": "...",
    "body": "...",
    "word_count": 850,
    "compliance_status": "pending",
    "research_ref": "dp-research-uuid"
  },
  "dry_run": false
}

# Response
{
  "node_id": "kg-node-uuid",
  "ingest_queued": false,
  "provenance": {
    "tenant": "nextchapter",
    "produced_by": "blog-agent",
    "workflow_run_id": "wf-uuid-hier"
  }
}
```

```bash
# DP auflösen (lesen)
GET /v1/dataproduct/resolve/{dp_id}?tenant_id=nextchapter

# Response
{
  "dp_id": "...",
  "node_type": "blog:BlogDraft",
  "payload": {...},
  "provenance": {...},
  "related_dps": [...]   # Aus KG: abgeleitete + referenzierte DPs
}
```

---

## DP-Provenienz im Knowledge Graph

```
AgentRun ──── PRODUCED ──── BlogDraft ──── DERIVED_FROM ──── ResearchSession
    │                           │
    └── TRIGGERED_BY ──── Schedule    └── COMPLIANCE_PENDING ──── ComplianceReport
                                                    │
                                         (nach Freigabe)
                                                    │
                                   BlogDraft ──── COMPLIANCE_CLEARED ──── ComplianceReport
                                       │
                                  PUBLISHED_TO
                                       │
                                   BlogPublished
```

Diese Kette macht jeden Output nachvollziehbar: «Welcher Agent hat wann was aus welchem Input produziert?»
