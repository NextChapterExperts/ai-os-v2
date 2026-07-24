# AI-OS v2 — Agent-SDK: Der Contract

**Stand:** Juli 2026 · **Verwandt:** [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) · [03-DATENPRODUKTE.md](03-DATENPRODUKTE.md)  
**Code:** `sdk/` im Repository-Root

---

## Das Kernprinzip

> **Jeder Agent ist ein Contract, kein Skript.**

In v1 konnten Agenten Datenprodukte umgehen, direkt auf Datenbanken schreiben und MCP ignorieren.  
In v2 macht das SDK solche Verletzungen zum **Fehler bei Instanziierung** — nicht zum stillen Bug in Produktion.

---

## Was der Contract fordert

```
┌──────────────────────────────────────────────────────────┐
│  Agent-Contract (jeder Agent muss erfüllen)              │
│                                                          │
│  1. agent_id    — eindeutige, stabile Kennung            │
│  2. version     — Semantic Versioning (Major.Minor.Patch)│
│  3. input_schema  — Pydantic-Klasse (erbt DataProduct)   │
│  4. output_schema — Pydantic-Klasse (erbt DataProduct)   │
│  5. run()       — Kernlogik, nur self.mcp für ext. Calls │
│  6. Tenant-Kontext — self.ctx immer explizit              │
│                                                          │
│  execute() — vom Framework aufgerufen, nie selbst:       │
│     → Input validieren                                   │
│     → run() aufrufen                                     │
│     → Output validieren + DP committen                   │
│     → Skill-Hook aufrufen                                │
└──────────────────────────────────────────────────────────┘
```

---

## AgentBase — Vollständige API

```python
# sdk/agent_base.py

class AgentBase(ABC, Generic[InputDP, OutputDP]):
    """
    Basisklasse für alle AI-OS v2-Agenten.

    Pflichtfelder (müssen in Subklasse überschrieben werden):
        agent_id:      str        — z.B. "research-agent"
        version:       str        — z.B. "2.0.0"
        input_schema:  type       — Pydantic-Klasse(DataProduct)
        output_schema: type       — Pydantic-Klasse(DataProduct)

    Methoden:
        run(input_dp)     — Kernlogik implementieren
        execute(input_dp) — Framework-Wrapper, NICHT überschreiben

    Attributes:
        self.ctx   — TenantContext (Tenant-ID, Policies, Budget, DP-Client)
        self.mcp   — MCPAdapter   (einziger Weg für externe Calls)
        self.skills — SkillStore  (Skill-Dokumente lesen/schreiben)
    """

    agent_id: ClassVar[str]
    version: ClassVar[str]
    input_schema: ClassVar[type[InputDP]]
    output_schema: ClassVar[type[OutputDP]]

    def __init__(
        self,
        ctx: TenantContext,
        mcp: MCPAdapter,
        skill_hook: SkillHook | None = None,
    ):
        self._validate_contract()
        self.ctx = ctx
        self.mcp = mcp
        self.skill_hook = skill_hook or SkillHook.noop()

    @abstractmethod
    async def run(self, input_dp: InputDP) -> OutputDP:
        """
        Kernlogik des Agenten.

        Regeln:
        - Nur self.mcp für externe Calls (HTTP, MCP-Server)
        - Kein direkter DB-Zugriff (Qdrant, Postgres, Letta)
        - Tenant-ID immer von self.ctx.tenant_id
        - LLM-Calls via self.ctx.llm (LiteLLM-Router)
        """
        ...

    async def execute(self, input_dp: InputDP | dict) -> OutputDP:
        """Framework-Wrapper — NICHT in Subklasse überschreiben."""
        validated = self.input_schema.model_validate(input_dp)
        result = await self.run(validated)
        validated_output = self.output_schema.model_validate(result)
        await self.ctx.dp_client.commit(validated_output)
        await self.skill_hook.post_run(
            agent_id=self.agent_id,
            input_dp=validated,
            output_dp=validated_output,
            ctx=self.ctx,
        )
        return validated_output
```

---

## Einen neuen Agenten schreiben

### Schritt 1: Scaffolding

```bash
# Neuen Agenten anlegen
python -m sdk.cli new-agent my-new-agent --tenant nextchapter

# Erzeugt:
# agents/my-new-agent/
#   agent.py          ← Implementierung
#   schema.yaml       ← KG-Schema-Einträge
#   README.md         ← Dokumentation
#   requirements.txt
```

### Schritt 2: Input/Output DataProducts definieren

```python
# agents/my-new-agent/agent.py
from sdk.dataproduct import DataProduct
from sdk.agent_base import AgentBase

class MyInput(DataProduct):
    """Was der Agent als Input bekommt."""
    query: str
    depth: Literal["quick", "deep"] = "quick"
    # tenant_id und produced_by werden von DataProduct geerbt

class MyOutput(DataProduct):
    """Was der Agent als Output produziert."""
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str] = []
    # Wo soll das DP gespeichert werden?
    storage_target: list[str] = ["G", "L1"]  # Knowledge Graph + Qdrant
    ingest_recommended: bool = True
```

### Schritt 3: Agenten-Logik implementieren

```python
class MyAgent(AgentBase[MyInput, MyOutput]):
    agent_id = "my-new-agent"
    version = "1.0.0"
    input_schema = MyInput
    output_schema = MyOutput

    async def run(self, input_dp: MyInput) -> MyOutput:
        # ✅ Externe Calls: ausschließlich self.mcp
        search_results = await self.mcp.call(
            server="web_search",
            tool="search",
            arguments={"q": input_dp.query, "num": 5},
        )

        # ✅ L1-Suche: auch über MCP
        vector_results = await self.mcp.call(
            server="qdrant_search",
            tool="search",
            arguments={
                "q": input_dp.query,
                "k": 3,
                "tenant_id": self.ctx.tenant_id,  # ← immer explizit
            },
        )

        # ✅ Company Brain lesen: nur MCP kg (P5/P18) — kein Direct-SQL
        related = await self.mcp.call(
            server="kg",
            tool="traverse",
            arguments={
                "entity": input_dp.query,
                "tenant_id": self.ctx.tenant_id,
                "hops": 2,
                "type_filter": ["org:*", "blog:*"],
            },
        )
        # ❌ verboten: kg.upsert_node / upsert_edge aus Fach-Agenten
        #    Graph-Writes nur indirekt: Output-DataProduct → DP-Commit

        # ✅ LLM-Call: über ctx.llm (LiteLLM-Router)
        summary = await self.ctx.llm.complete(
            prompt=f"Fasse zusammen: {search_results} und {vector_results}",
            compute_mode=self.ctx.compute_mode,
        )

        return MyOutput(
            tenant_id=self.ctx.tenant_id,       # ← Pflicht
            produced_by=self.agent_id,           # ← Pflicht
            summary=summary.text,
            confidence=summary.confidence,
            sources=[r["url"] for r in search_results],
        )
```

### Schritt 4: Contract-Tests laufen lassen

```bash
python -m pytest sdk/tests/test_contract.py -k "my-new-agent" -v
# Prüft: agent_id, version, input_schema, output_schema, execute() committet DP
```

---

## Häufige Fehler und wie das SDK sie verhindert

### Fehler 1: Kein agent_id

```python
class BrokenAgent(AgentBase):
    # agent_id fehlt!
    input_schema = MyInput
    output_schema = MyOutput
    async def run(self, input_dp): return None

agent = BrokenAgent(ctx, mcp)
# → ValueError: BrokenAgent: agent_id fehlt
```

### Fehler 2: Direkter DB-Zugriff

```python
# sdk/mcp_adapter.py — MCPAdapter patcht requests-Import zur Laufzeit
# Ein direkter import requests + requests.get() außerhalb von MCPAdapter
# wirft einen ContractViolationError
```

### Fehler 2b: Graph-Write ohne DataProduct (P18)

```python
# ❌ Fach-Agent
await self.mcp.call("kg", "upsert_node", {"type": "org:Decision", ...})
# → Cap/Policy: nur dp-service + memory-agent

# ✅ Stattdessen Output-DP zurückgeben; Orchestrator committed
return OrgDecision(tenant_id=..., decision_id=..., status="proposed", ...)
```

### Fehler 3: Tenant-ID aus dem Kontext ignorieren

```python
# DataProduct-Validator prüft: tenant_id darf nicht leer sein
MyOutput(
    tenant_id="",          # → ValidationError: tenant_id darf nicht leer sein
    produced_by=self.agent_id,
    summary="...",
)
```

### Fehler 4: Output-DP nicht vom richtigen Typ

```python
async def run(self, input_dp: MyInput) -> MyOutput:
    return {"summary": "..."  }  # dict statt MyOutput

# → execute() wirft ValidationError bei output_schema.model_validate(result)
```

---

## MCPAdapter — Externe Calls kapseln

```python
# sdk/mcp_adapter.py
class MCPAdapter:
    """
    Einziger erlaubter Weg für Agenten um externe Calls zu machen.

    Leitet alle Calls an den MCP-Gateway weiter.
    Caps und Audit werden dort durchgesetzt.
    """

    def __init__(self, gateway_url: str, tenant_id: str, agent_id: str):
        self._gateway = gateway_url
        self._tenant_id = tenant_id
        self._agent_id = agent_id

    async def call(
        self,
        server: str,
        tool: str,
        arguments: dict,
    ) -> dict:
        """
        Ruft ein MCP-Tool auf.

        Args:
            server:    Server-ID aus mcp-servers.yaml (z.B. "web_search")
            tool:      Tool-Name des Servers (z.B. "search")
            arguments: Tool-spezifische Parameter

        Returns:
            Tool-Ergebnis als dict

        Raises:
            MCPCapExceededError:    Rate-Cap überschritten
            MCPServerNotAllowed:    Server nicht für Tenant erlaubt
            MCPToolNotFound:        Tool existiert nicht auf Server
        """
        response = await httpx.post(
            f"{self._gateway}/v1/call",
            json={
                "server_id": server,
                "tool_name": tool,
                "arguments": arguments,
            },
            headers={
                "X-Tenant-ID": self._tenant_id,
                "X-Agent-ID": self._agent_id,
            },
        )
        if response.status_code == 429:
            raise MCPCapExceededError(server, tool)
        if response.status_code == 403:
            raise MCPServerNotAllowed(server, self._tenant_id)
        response.raise_for_status()
        return response.json()["result"]
```

---

## TenantContext — Alles was ein Agent braucht

```python
# sdk/tenant_context.py
@dataclass
class TenantContext:
    tenant_id: str
    compute_mode: Literal["sovereign", "balanced", "premium"]
    active_packages: list[str]          # Welche SKUs sind installiert?
    guardrails_policy: GuardrailsPolicy

    # Clients — dependency-injected, niemals direkt importieren
    dp_client: DataProductClient        # DP committen/auflösen
    llm: LiteLLMClient                 # LLM-Calls (model-agnostisch)
    skill_store: SkillStore             # Skills lesen

    @classmethod
    def for_tenant(cls, tenant_id: str) -> "TenantContext":
        """Factory — lädt alles aus config/ + Datenbank."""
        ...
```

---

## Skill-Hook — Automatische Skill-Destillation

```python
# sdk/skill_hook.py
class SkillHook:
    """
    Wird von execute() nach jedem erfolgreichen Run aufgerufen.
    Bei komplexen Tasks: Skill-Dokument destillieren oder verfeinern.
    """

    async def post_run(
        self,
        agent_id: str,
        input_dp: DataProduct,
        output_dp: DataProduct,
        ctx: TenantContext,
    ) -> None:
        run_complexity = self._estimate_complexity(input_dp, output_dp)
        if run_complexity < COMPLEXITY_THRESHOLD:
            return  # Zu einfach für einen Skill

        existing = await ctx.skill_store.find_by_agent_and_input(
            agent_id, input_dp
        )
        if existing:
            await self._refine_skill(existing, input_dp, output_dp, ctx)
        else:
            await self._create_skill(agent_id, input_dp, output_dp, ctx)
```

---

## Agent-Template (Scaffolding-Ausgabe)

```python
# agents/{name}/agent.py — Template
"""
{NAME} Agent — AI-OS v2

Zweck: [Beschreibung was der Agent macht]
SKU:   AIOS-PACK-{NAME}
"""
from sdk.agent_base import AgentBase
from sdk.dataproduct import DataProduct
from typing import Literal

class {Name}Input(DataProduct):
    # TODO: Felder definieren
    pass

class {Name}Output(DataProduct):
    # TODO: Felder definieren
    storage_target: list[str] = ["G"]
    ingest_recommended: bool = False

class {Name}Agent(AgentBase[{Name}Input, {Name}Output]):
    agent_id = "{name}-agent"
    version = "1.0.0"
    input_schema = {Name}Input
    output_schema = {Name}Output

    async def run(self, input_dp: {Name}Input) -> {Name}Output:
        # TODO: Implementierung
        # Nur self.mcp für externe Calls
        # self.ctx.llm für LLM-Calls
        # self.ctx.tenant_id für Tenant-Kontext
        raise NotImplementedError
```

---

## Contract-Tests (alle Agenten müssen bestehen)

```bash
# Alle Contract-Tests
python -m pytest sdk/tests/ -v

# Für einen spezifischen Agenten
python -m pytest sdk/tests/ -k "research" -v

# Erwartet: 10/10 Tests grün
```

| Test-ID | Prüfung |
|---------|---------|
| CONTRACT-01 | agent_id fehlt → ValueError |
| CONTRACT-02 | version fehlt → ValueError |
| CONTRACT-03 | input_schema fehlt → ValueError |
| CONTRACT-04 | output_schema fehlt → ValueError |
| CONTRACT-05 | execute() committed immer ein DP |
| CONTRACT-06 | execute() ruft skill_hook auf |
| CONTRACT-07 | tenant_id leer → ValidationError |
| CONTRACT-08 | Output falscher Typ → ValidationError |
| CONTRACT-09 | MCPAdapter kapselt alle externen Calls |
| CONTRACT-10 | TenantContext wird nicht modifiziert |
