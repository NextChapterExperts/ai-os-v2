# AI-OS — Framework-Vergleich & Strategische Bewertung

**Stand:** Juli 2026 · **Nr. 18** · **Autor:** Peter / NCE  
**Verwandte Dokumente:** [00-VISION.md](00-VISION.md) · [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) · [11-NAECHSTE-SCHRITTE.md](11-NAECHSTE-SCHRITTE.md) · [19-OPTIMAL-ARCHITEKTUR.md](19-OPTIMAL-ARCHITEKTUR.md)

---

## Kernfrage

> Wäre ein bekanntes Agent-Framework (Hermes Agent, OpenClaw, LangGraph, CrewAI, AutoGen) eine bessere Grundlage als der individuelle AI-OS-Ansatz?

**Kurz-Urteil: Nein — aber mit zwei konkreten Ausnahmen.**  
Kein einzelnes Framework löst das, was AI-OS lösen soll: eine deploybare, multi-tenant-fähige KI-Plattform mit Domain-Pipelines, UI, LLM-Router, Compliance und Paketsystem. Die Frameworks spielen in einer anderen Liga — nicht schlechter, anders positioniert.

---

## 1. Bewertete Frameworks

### 1.1 Hermes Agent *(Nous Research, Feb 2026, MIT)*

**Profil:**  
Self-hosted, persistent Memory, autonomer Skill-Loop (Markdown-basiert), eingebauter Cron-Scheduler, Sub-Agent-Delegation, 16+ Messaging-Plattformen, vollständig model-agnostisch (Ollama, OpenAI, OpenRouter).

**Was Hermes besser macht als AI-OS:**

| Feature | Hermes | AI-OS |
|---------|--------|-------|
| **Skill-Loop** | Kern-Feature — kampferprobt | P1-Baustelle «Skill-Loader» offen |
| **Scheduler / Cron** | Eingebaut, natural language | P2-Blocker «scheduler-agent» offen |
| **Skill-Verfeinerung** | Automatisch bei Wiederholung | Nicht implementiert |
| **Session-Recall** | FTS5 + LLM-Summarization | Grundlagen da, kein Cross-Session-Recall |

**Was AI-OS besser macht:**

- **Multi-Tenant / SKU-Pakete:** Hermes ist single-user, kein Paketsystem, keine Tenant-Isolation.
- **Produktions-UI:** Hermes hat keine Next.js-Console.
- **MCP-Gateway als Konnektivitäts-Layer:** Hermes nutzt direkte Tool-Bindings.
- **Guardrails / Compliance:** Kein Policy-Layer in Hermes.
- **Knowledge Graph / RAG:** Kein Qdrant, kein GraphRAG.
- **LLM-Router / FinOps:** Kein LiteLLM-Äquivalent.

**Empfehlung:** Hermes's **Skill-Loop als Blaupause** für AI-OS's Skill-Loader (P1) verwenden. Nicht ersetzen — konkret inspirieren lassen.

---

### 1.2 OpenClaw *(Nov 2025, ~383k GitHub-Stars, TypeScript)*

**Profil:**  
Personal AI Assistant, Gateway für 50+ Messaging-Plattformen (WhatsApp, iMessage, Telegram, Discord, Signal …), Multi-Agent-Routing, Plugin-Architektur, Voice, Live Canvas, Companion-Apps (macOS/iOS/Android). Viral-Growth: #1 GitHub-Projekt in 60 Tagen.

**Was OpenClaw besser macht:**

- **Multi-Channel-Messaging** ist das Herzstück — aus einer Gateway-Instanz.
- **Companion-App-Ökosystem** (macOS/iOS/Android) ist einzigartig in dieser Reife.
- **Community-Velocity:** Release alle 2 Tage, 1.200+ Contributors.

**Was AI-OS besser macht:**

- OpenClaw ist ein **Personal Assistant**, keine Business-Plattform.
- Kein Paketsystem, keine Tenant-Isolation, keine Guardrails, kein RAG-Stack.
- **Zu jung für Enterprise:** 6.383 offene Issues, 5 Monate alt, kein Compliance-Layer.
- TypeScript-only — kein Python-Ökosystem für ML-Pipeline.

**Empfehlung:** Beobachten, nicht adoptieren. Wenn AI-OS ein Multi-Platform-Messaging-Feature braucht, OpenClaw-Kanal-Architektur als Referenz nehmen. MCP bleibt die bessere Konnektivitäts-Strategie.

---

### 1.3 LangGraph *(LangChain, v1.1.3, Apache 2.0)*

**Profil:**  
Gerichtete State-Machine-Orchestrierung, explizites Checkpointing, Human-in-the-Loop via `interrupt()`, LangSmith-Observability, parallele Branches, Retry-Logic. #1 Production-Framework 2026. Enterprise: Klarna, Uber, LinkedIn. 30–40 % weniger Tokens als CrewAI.

**Was LangGraph besser macht:**

- **Workflow-Orchestrierung als Industriestandard:** Typed State, Checkpoints, Audit-Trails — alles eingebaut.
- AI-OS's eigener Workflow-Runner ist ein Subset dieser Fähigkeiten.
- **Observability** via LangSmith ist deutlich weiter als AI-OS's Monitor.

**Was AI-OS besser macht:**

- LangGraph ist eine **Library**, kein Stack: kein UI, kein Memory-Layer (Qdrant/Letta), kein Paketsystem, kein LLM-Router, keine Tenant-Isolation.
- AI-OS hat alles integriert deployed.

**Empfehlung:** Wenn AI-OS's Workflow-Runner refactored wird oder der `scheduler-agent` gebaut wird: **LangGraph als Engine einbetten** statt selbst bauen. Kein Ersatz für die Gesamt-Plattform.

---

### 1.4 CrewAI *(v1.12, MIT)*

**Profil:**  
Role-based Crews (Researcher + Writer + Editor), schnelles Prototyping, deklarativ, MCP- und A2A-Support ab v1.10. 60 % Fortune-500-Einsatz. Schwach bei Observability und Token-Effizienz (3× overhead bei einfachen Tasks).

**Was CrewAI könnte:**

- Blog-Agent-Workflow (Research → Draft → Compliance → Publish) wäre ein natürlicher CrewAI-Fit.
- AI-OS hat diesen Workflow aber bereits selbst gebaut.

**Empfehlung:** Kein Handlungsbedarf. CrewAI-Patterns für den Blog-Orchestrator als konzeptuelle Referenz verwenden — aber nicht als Dependency einziehen.

---

### 1.5 AutoGen / Microsoft Agent Framework *(2026)*

**Profil:**  
Seit 2026 gespalten in **AG2** (community, maintenance-only) und **Microsoft Agent Framework** (MAF, enterprise .NET/Azure). Stärke: konversationelle Multi-Agent-Loops, Code-Execution-Sandbox.

**Bewertung:**  
Irrelevant für AI-OS's Python/Docker/Linux-Stack. MAF nur relevant für Azure-heavy Enterprise-Umgebungen.

**Empfehlung:** Kein Handlungsbedarf.

---

## 2. Feature-Matrix

| Dimension | AI-OS | Hermes | OpenClaw | LangGraph | CrewAI |
|-----------|-------|--------|----------|-----------|--------|
| Multi-Tenant / SKU-Pakete | ✅ Kern-Feature | — | — | — | — |
| Next.js Console / UI | ✅ produktiv | — | Browser-UI | — | — |
| MCP Gateway | ✅ M1 | — | Partiell | Partiell | ✅ v1.10 |
| **Skill-Loader / Skill-Loop** | ⚠️ P1 offen | ✅ Kern-Feature | ✅ | — | — |
| **Scheduler / Cron** | ⚠️ P2 offen | ✅ eingebaut | ✅ | Partiell | — |
| Persistent Memory L1 (Vektor) | ✅ Qdrant | ✅ FTS5 | — | Partiell | — |
| Persistent Memory L2/L3 | ✅ Letta | ✅ Honcho | — | — | — |
| Knowledge Graph / GraphRAG | ✅ (UI offen) | — | — | — | — |
| LLM-Router / FinOps | ✅ LiteLLM | — | — | — | — |
| Guardrails / Compliance | ✅ L1/L2 | — | Partiell | — | — |
| Deterministische Pipeline | ✅ Design-Ziel | — | — | ✅ | — |
| Multi-Platform Messaging | — | ✅ 16+ | ✅ 50+ | — | — |
| Produktionsreife | Pilot ~75 % | Mittel | Niedrig (5 Mo.) | Hoch | Mittel |
| A2A-Protokoll | — | — | — | Partiell | ✅ |

---

## 3. Strategisches Urteil

### Warum AI-OS nicht ersetzt werden sollte

Alle bewerteten Frameworks lösen das «**ein Agent für eine Person**»-Problem oder das «**Workflow-Library**»-Problem. AI-OS löst das «**Produkt für mehrere Kunden**»-Problem — mit Paketsystem, UI, Governance, Domain-Pipelines und deploybarem Stack.

Wer LangGraph + Qdrant + Letta + LiteLLM + Next.js + Tenant-Isolation selbst verdrahtet, baut wieder AI-OS.

### Zwei konkrete Handlungsempfehlungen

**Handlung 1 — Hermes Skill-Loop als Blaupause (P1)**  
Der Hermes-Skill-Loop ist genau das, was AI-OS als Skill-Loader braucht. Konkrete Übernahme:
1. Nach komplexem Task automatisch ein Markdown-Skill-Dokument per LLM destillieren.
2. Skill-Index (Vektor + FTS5) für Kontext-Abruf.
3. Skill refinement: bestehende Skills verbessern, nicht ersetzen.
4. Kompatibilität mit `agentskills.io`-Standard prüfen (AI-OS's Cursor-Skills folgen schon ähnlichem Muster).

**Handlung 2 — LangGraph als Workflow-Runner-Engine (optional, bei Refactoring)**  
Wenn der Workflow-Runner oder der `scheduler-agent` die nächste Iteration bekommt, LangGraph als Engine einbetten statt selbst bauen. Gibt Checkpointing, Retry-Logic und Audit-Trails geschenkt — und ist in Produktion bei Enterprise-Kunden battle-tested.

---

## 4. Weiterführend

- [19-OPTIMAL-ARCHITEKTUR.md](19-OPTIMAL-ARCHITEKTUR.md) — Ziel-Architektur auf Basis dieser Bewertung
- [12-ADR-D8-HYBRID-RUNTIME.md](12-ADR-D8-HYBRID-RUNTIME.md) — Skills + MCP ADR
- [ROADMAP.md](../../ROADMAP.md) — Operative Prioritäten
