# AI-OS v2 — Marktvergleich: Gibt es ähnliche Ansätze?

**Erstellt:** 2026-07-13  
**Methode:** Web- und GitHub-Recherche nach self-hosted, souveränen KI-Betriebssystemen mit RAG, Knowledge Graph, MCP, Skill-Loop und Multi-Tenant.

## Kurzfazit

**Ja, die Kategorie existiert** — und sie ist 2026 erwachsen geworden. „Agent OS" / „AI OS" / „sovereign AI platform" ist ein etablierter Markt mit Open-Source-Projekten und kommerziellen EU-Anbietern. **Kein einzelnes Projekt deckt jedoch die exakte AI-OS-v2-Kombination ab**: deterministische Hülle + typisierte Datenprodukte als einziger Datenpfad + erzwungener Agent-Contract (SDK) + Skill-Loop + Multi-Tenant-SKU-Pakete + Ollama-Default. Die Einzelbausteine sind aber alle am Markt — v2 ist eine **Integrationsleistung**, keine Erfindung.

---

## 1. Direkteste Überschneidung: Cognithor (Open Source)

**[github.com/Alex8791-cyber/cognithor](https://github.com/Alex8791-cyber/cognithor)** — Apache 2.0, Python 3.12+

Das mit Abstand ähnlichste Projekt. Bezeichnet sich selbst als „local-first autonomous agent operating system".

| Feature | Cognithor | AI-OS v2 |
|---------|-----------|----------|
| Positionierung | Agent OS, local-first | KI-Betriebssystem, souverän |
| Memory | **6-Tier** (Core, Episodic, Semantic KG, Procedural/Skills, Working, Tactical) | L0–L3 + G + SK + A |
| Suche | **4-Kanal Hybrid** (BM25 + Vektor + KG-Traversal + hierarchisch) | Unified Search (L1 + G + SK + A) |
| LLM | Ollama/LM Studio + 19 Provider | Ollama-Default + OpenRouter |
| Skills | Agent-Packs-Marktplatz | SKU-Fach-Agenten + Skill-Loop |
| MCP | 145 MCP-Tools | MCP-Gateway |
| Telemetrie | Zero, GDPR | Souverän, DSGVO |

**Unterschied:** Cognithor ist Single-User-fokussiert (persönlicher Assistent, Desktop-Steuerung via Computer Use). AI-OS v2 ist **Multi-Tenant-Produkt** mit erzwungenem Contract und deterministischer Governance-Hülle. Cognithors Skill-Marktplatz ähnelt euren SKU-Paketen stark.

---

## 2. Open-Source Agent-Plattformen (Feature-Nachbarn)

| Projekt | Quelle | Stack | Überschneidung |
|---------|--------|-------|----------------|
| **JARVIS** | [github.com/hyhmrright/JARVIS](https://github.com/hyhmrright/JARVIS) | FastAPI · **LangGraph** · Postgres · Qdrant · MinIO · Prometheus/Grafana | „Self-hosted AI OS": RAG, Multi-Tenant-Workspaces, Skill-Market, Audit-Logs, `docker compose up` — **sehr nah an eurer Deployment-Philosophie** |
| **Synesis** | [github.com/supernovae/synesis](https://github.com/supernovae/synesis/) | Kubernetes · NornicDB · OpenFGA | Graph-native RAG, Planner→Retrieval→Writer→Critic-Pipeline, Model-Governance, MCP-Exposition, HITL-Review |
| **Synkora** | [github.com/getsynkora/synkora-ai](https://github.com/getsynkora/synkora-ai) | **LiteLLM** · Qdrant · **Langfuse** | Multi-Tenant, RAG, MCP, HITL-Gates, Stripe-Billing, **Langfuse-Observability** — fast identischer Infrastruktur-Stack wie AI-OS v2 |
| **Nexora** | [github.com/ParendumOU/Nexora](https://github.com/ParendumOU/Nexora) | pgvector · ~46 LLM-Provider | Agent-Orchestrierung, Sub-Agent-Delegation, semantisches Memory, Marktplatz, Multi-Tenant (MIT) |
| **Olla Nest** | [github.com/ashokramcse/olla-nest](https://github.com/ashokramcse/olla-nest) | Ollama Auto-Router | **Automatisches Modell-Routing** lokal↔Cloud, **Privacy-Gate** (PII blockt externes Routing), RBAC, Deep Research — spiegelt euer Model-Gateway + Guardrails |
| **FIM One** | [github.com/fim-ai/fim-one](https://github.com/fim-ai/fim-one) | FastAPI · Next.js · LanceDB | Enterprise-Konnektoren, Multi-Tenant, Ollama-Support (eingeschränkte Lizenz) |

**Beobachtung:** Der Kern-Stack von AI-OS v2 (FastAPI + LangGraph + LiteLLM + Qdrant + Postgres + Langfuse + Ollama + MCP) ist **de-facto Industriestandard 2026** geworden. Synkora und JARVIS nutzen fast dieselbe Kombination.

---

## 3. Kommerzielle / EU-souveräne Plattformen

| Anbieter | Quelle | Kern | Überschneidung |
|----------|--------|------|----------------|
| **Verisa AI** (Entel, HU) | [verisa.ai](https://verisa.ai/en) | Graph-native Reasoning, SHA-3 hash-chained Audit, EU AI Act, air-gapped | Graph-Verifikation, lückenlose Traceability, On-Prem |
| **MoE Codex** | [moe-codex.org](https://moe-codex.org/) | „EU-Alternative zu Palantir Foundry", Sovereign LLM Gateway + GraphRAG, OpenLineage | Data-Catalog, Lineage, €0/Token auf eigener HW, Apache 2.0 |
| **ArcaQ** (Talentys) | [arcaq.com](https://www.arcaq.com/) | **100% On-Prem, Ollama**, Apache Jena KG (RDF/SPARQL), PII-Detection, MCP-Gateway | „LLM nur zum Formatieren, nicht zum Antworten" — sehr nah an eurer deterministischen Hülle (P4) |
| **Neksus Core** | [neksus.ai/core](https://neksus.ai/core/) | On-Prem „Enterprise Brain", KG + Org-LLM, **Redaction-Gateway** vor externen Modellen | Redaction-Gateway = euer Anonymizer-Muster |
| **Xinity** | [xinity.ai](https://xinity.ai/) | OpenAI-kompatibel, Multi-Model-Routing, Audit-Log auf AI-Act-Artikel gemappt | Model-Gateway + FinOps |

**Beobachtung:** Der souveräne EU-Markt validiert eure These vollständig — **On-Prem + Ollama + KG + Audit + Redaction-Gateway** ist genau das Muster, das mehrere Anbieter unabhängig gewählt haben. Besonders **ArcaQ** (Ollama, KG, „LLM formatiert nur") und **Neksus** (Redaction-Gateway) bestätigen AI-OS-Prinzipien P4 und den Anonymizer-Router.

---

## 4. Fundament-Bausteine (was ihr korrekt gewählt habt)

| Baustein | Quelle | Bestätigung |
|----------|--------|-------------|
| **LangGraph** | [github.com/langchain-ai/langgraph](https://github.com/langchain-AI/langgraph) | Industriestandard für stateful Agenten (Klarna, Replit, Elastic); Durable Execution, HITL, Checkpoints — exakt eure P7-Begründung |
| **LangChain MCP Adapters** | [github.com/langchain-ai/langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) | MCP-Tools in LangGraph, `MultiServerMCPClient` — Blaupause für euer MCP-Gateway |
| **Graphiti** (Zep) | [github.com/getzep/graphiti](https://github.com/getzep/graphiti) | Temporale KGs als Agent-Memory, Episode-Ingestion + Entity-Reconciliation — Referenz für euer Memory-Flywheel (L2/L3) |
| **Onyx** | [onyx.app](https://onyx.app/insights/enterprise-rag-platforms-2026) | Open-Source Enterprise-RAG, air-gapped, 37.000+ User bei UC San Diego — Benchmark für Skalierung |

---

## 5. Architektur-Trend, der AI-OS v2 bestätigt

Die Recherche zeigt ein 2026 neu benanntes Muster: **Cognitive-Executive Separation (CES)** ([Atlan, 2026](https://atlan.com/know/ai-memory-vs-rag-vs-knowledge-graph/)):

> Ein *untrusted „agent process"* schlägt Graph-Mutationen vor, ein *deterministischer „engine process"* validiert sie gegen eine strikte Ontologie — so bleibt der Graph frei von Halluzinationen und non-compliant Daten.

**Das ist exakt AI-OS-Prinzip P4 (Determinismus in der Hülle) + P8 (Agent-Contract) + P9 (alles typisiert in die DB).** Euer Ansatz liegt also nicht nur im Trend — er hat einen Namen im Markt.

---

## 6. Was AI-OS v2 unterscheidet (Alleinstellung)

Kein gefundenes Projekt kombiniert **alle** folgenden Punkte:

1. **Typisierte Datenprodukte als einziger Datenpfad** — die meisten erlauben Agenten direkten DB-Zugriff. v2 erzwingt DP-Commit über SDK.
2. **Agent-Contract als Instanziierungs-Fehler** — andere haben „Tools/Skills", aber keinen erzwungenen Pydantic-Contract mit Input/Output-Schema.
3. **Skill-Loop mit Versionierung + Refinement** — Cognithor/Nexora haben Skill-Marktplätze, aber keine automatische Destillation + Verfeinerung nach jedem Task.
4. **Platform-Gate vor Fach-Agenten** — strikte Build-Reihenfolge (P10) fand sich bei keinem anderen Projekt.
5. **SKU-Paket-Modell für mehrere Kunden** — die meisten OSS-Projekte sind Single-Org; kommerzielle sind proprietär.

**Fazit:** AI-OS v2 ist **kein Nischen-Sonderweg**, sondern eine besonders **disziplinierte, governance-first Integration** bewährter 2026-Bausteine. Die größten Risiken sind nicht technischer Natur (Stack ist Standard), sondern **Differenzierung** gegenüber Cognithor (OSS) und ArcaQ/Verisa (EU-kommerziell).

---

## Quellen

**Open Source — Agent OS / Plattformen**
- Cognithor — https://github.com/Alex8791-cyber/cognithor
- JARVIS — https://github.com/hyhmrright/JARVIS
- Synesis — https://github.com/supernovae/synesis/
- Synkora — https://github.com/getsynkora/synkora-ai
- Nexora — https://github.com/ParendumOU/Nexora
- Olla Nest — https://github.com/ashokramcse/olla-nest
- FIM One — https://github.com/fim-ai/fim-one

**Fundament-Frameworks**
- LangGraph — https://github.com/langchain-ai/langgraph
- LangChain MCP Adapters — https://github.com/langchain-ai/langchain-mcp-adapters
- Graphiti (Zep) — https://github.com/getzep/graphiti
- Memgraph + LangGraph + MCP — https://memgraph.com/blog/end-to-end-llm-agents-with-memgraph-langgraph-mcp

**Kommerziell / EU-souverän**
- Verisa AI — https://verisa.ai/en
- MoE Codex — https://moe-codex.org/
- ArcaQ (Talentys) — https://www.arcaq.com/
- Neksus Core — https://neksus.ai/core/
- Xinity — https://xinity.ai/
- Onyx (Enterprise RAG 2026) — https://onyx.app/insights/enterprise-rag-platforms-2026

**Architektur-Analysen**
- Atlan — AI Memory vs RAG vs Knowledge Graph (2026) — https://atlan.com/know/ai-memory-vs-rag-vs-knowledge-graph/
- The Neural Maze — Building Agent Memory with Knowledge Graphs — https://theneuralmaze.substack.com/p/building-agent-memory-with-knowledge

---

## 7. Was AI-OS v2 konkret übernehmen sollte

Priorisiert nach Nutzen für die vier Ziele (Kosten · Qualität · Skalierung · Erweiterbarkeit). Alle Muster fügen sich in den bestehenden Stack ein — kein Technologiewechsel.

### Übernehmen (hoher Nutzen, passt zur Architektur)

| # | Muster | Quelle | Wohin in AI-OS v2 | Ziel |
|---|--------|--------|-------------------|------|
| 1 | **PGE-Trinity: Planner → Gatekeeper → Executor** | Cognithor | Orchestrator + Guardrails formalisieren: LLM plant, deterministischer Gatekeeper validiert jeden Tool-Call (GREEN/YELLOW/ORANGE/RED), Executor sandboxed | Qualität, Sicherheit |
| 2 | **Observer Audit Layer** — Post-Response-Qualitätscheck (Halluzination, Sycophancy, Faulheit, Tool-Ignoranz), triggert Regeneration | Cognithor | Neuer Platform-Schritt nach jedem Agent-Run; nutzt lokales Modell → **kostenlos** | Qualität |
| 3 | **Hash-chained Audit (SHA-256, `prev_hash`)** | Cognithor, Verisa (SHA-3), MoE Codex | `A`-Schicht (`ai_os_log`) manipulationssicher machen — jeder Eintrag chained | Compliance, Skalierung |
| 4 | **Signed Run-Receipts / TRUST-Ledger** — provenance, cost (micro-USD), permission-scopes, cloud-escalation | Cognithor | Ergänzt P9 + FinOps: pro Workflow-Run ein signierter Beleg mit Kosten | Kosten, Compliance |
| 5 | **Redaction-/Privacy-Gateway vor Cloud-Call** | Neksus, Olla Nest, ArcaQ | Guardrails-Agent: PII-Scan blockt automatisch `balanced`/`premium`, erzwingt `sovereign` | Kosten, DSGVO |
| 6 | **Auto-Router mit Modell-Scoring** — jede Anfrage gegen erlaubte Modelle scoren, bestes automatisch wählen | Olla Nest | Model-Gateway: über feste Keyword-Regeln hinaus | Kosten, Qualität |
| 7 | **CAG (Cache-Augmented Generation)** — deterministische Prefixe für LLM-KV-Cache-Reuse | Cognithor | Bei wiederholten System-Prompts/Kontexten → weniger Tokens, schneller | Kosten |
| 8 | **Planner → Retrieval → Writer → Critic** Pipeline | Synesis | Blog-/Research-Workflows: eingebauter Critic-Node vor Human-Review | Qualität |

### Lernen (Konzept übernehmen, angepasst)

| # | Muster | Quelle | Lehre für AI-OS v2 |
|---|--------|--------|--------------------|
| 9 | **Skill-Marktplatz mit 5-Check-Validation + Ed25519-Signierung (TUF-Light)** | Cognithor | Wenn SKU-Pakete/Skills geteilt werden: Signierung + Validierungs-Pipeline von Anfang mitdenken |
| 10 | **Deterministic Replay** — Runs aufzeichnen und mit What-if-Diff erneut abspielen | Cognithor | LangGraph-Checkpoints dafür nutzen — Debugging + Regressionstests |
| 11 | **`_safe_call()`-Muster** — einheitliches Error-Handling statt stillem `except: pass`, mit Failure-Registry + Circuit-Breaker | Cognithor | SDK-weite Konvention im `AgentBase` |
| 12 | **ADRs (Architecture Decision Records)** | Cognithor | Passt zu „eine Implementierung": jede finale Entscheidung als ADR in `docs/` |
| 13 | **„LLM formatiert nur, generiert keine Fakten"** | ArcaQ | Verstärkt P13 — bei kritischen Antworten LLM nur zur Formulierung, Fakten aus KG/Retrieval |
| 14 | **OpenFGA / ABAC-Autorisierung in der Retrieval-Schicht** | Synesis, Neksus | Für Multi-Tenant Phase 6: Row-Level-Authz statt nur Namespace-Trennung |
| 15 | **Billing/Stripe + Quotas pro Tenant** | Synkora | Für das SKU-Produktmodell (docs/06) — Abrechnung early mitdenken |

### Nicht übernehmen (bewusst weglassen)

| Muster | Warum nicht |
|--------|-------------|
| 17 Messaging-Kanäle, Voice, Computer-Use, ARC-AGI-Benchmark (Cognithor) | Scope-Explosion — AI-OS v2 ist Produkt für Kunden, kein Experimentierkasten |
| Kubernetes-Control-Plane (Synesis) | Docker Compose reicht bis Enterprise; K8s erst wenn echter Bedarf |
| 46 LLM-Provider (Nexora) | Bewusste Entscheidung: nur Ollama + OpenRouter (P12) |
| Eigene Vektor-DB (NornicDB/LanceDB) | Qdrant ist gesetzt |

---

## 8. Wo die anderen (noch) besser sind

Ehrliche Einordnung — hier hat AI-OS v2 Nachholbedarf oder kann sich Reife abschauen:

| Bereich | Wer besser | Was konkret |
|---------|-----------|-------------|
| **Test-Reife** | Cognithor | 17.000+ Testfunktionen, 89 % Coverage-Gate, mypy --strict, nightly Audit-Burn-in. AI-OS v2 sollte Coverage-Gate + Property-Tests (Hypothesis) einführen |
| **Audit/Compliance-Tiefe** | Verisa, Cognithor, MoE Codex | Hash-chained Logs, signierte Belege, RFC-3161-Zeitstempel, EU-AI-Act-Artikel-Mapping, Source-Code-Escrow — v2 hat nur einfaches `ai_os_log` |
| **Retrieval-Qualität** | Verisa (94,7 % Hits@10 MultiHop-RAG), Cognithor (4-Kanal-Fusion) | v2s Unified Search sollte BM25 + Vektor + Graph + hierarchisch **mit Score-Fusion** kombinieren, nicht nur parallel abfragen |
| **Memory-Granularität** | Cognithor (6-Tier inkl. Working/Tactical) | v2 sollte „Working" (aktive Session) und „Tactical" (offene Ziele, Rollback) explizit ergänzen |
| **Skalierung erprobt** | Onyx (37.000+ User, air-gapped bei UC San Diego) | v2 ist noch nicht last-erprobt — Onyx zeigt, dass der Ansatz enterprise-skaliert |
| **Time-to-Value / Onboarding** | Cognithor (One-Click-Start), JARVIS (`docker compose up`) | v2s Platform-Gate ist gründlich, aber der erste Erfolg dauert länger — One-Command-Demo-Modus wäre gut |
| **DACH-Konnektoren** | Cognithor (sevDesk), FIM One | v2 könnte früh einen Buchhaltungs-/Steuer-Konnektor (sevDesk/DATEV) priorisieren |

**Kernlehre:** Die Konkurrenz ist bei **Testdisziplin, Audit-Kryptografie und Retrieval-Fusion** weiter. AI-OS v2 ist bei **Governance-Struktur (Contract, Datenprodukte, Platform-Gate)** und **Produktmodell (SKU, Multi-Tenant)** klarer. Die drei besten Sofort-Übernahmen: **PGE-Gatekeeper (1)**, **Observer Audit Layer (2)** und **hash-chained Audit (3)** — alle drei stärken Qualität und Compliance ohne neuen Technologie-Ballast.
