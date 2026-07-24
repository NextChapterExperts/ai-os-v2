# AI-OS v2 — Vision

**Stand:** Juli 2026 · **Basis:** [v1 00-VISION.md](../../1000-AI-OS/docs/platform/00-VISION.md)  
**Operativ:** [ROADMAP.md](../ROADMAP.md) · **Architektur:** [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md)

---

## In einem Satz

**AI-OS v2 ist ein state-of-the-art, souveränes KI-Betriebssystem:** Ausgeliefert als **Platform-VM** (*eine VM · eine Tür · ein Gedächtnis*). Eine deterministische Plattform-Hülle speichert, verknüpft und schützt Wissen als **Company Brain** (Single Source of Truth in K+G+kuratiertem L1) — nicht als persönlicher Second Brain. Alle LLM-Calls über das **Memory Gateway**; externe Chats (Gemini, Antigravity, …) über **Chat Capture** in denselben Speicher. Externe Konnektivität ausschließlich über **MCP**; jede Aktion hinterlässt typisierte **Datenprodukte** im **Knowledge Graph**; jeder Agent wird durch einen **Contract** gezwungen.
---

## Die vier Ziele

| Ziel | Umsetzung |
|------|-----------|
| **Kosten sparen** | Ollama-Default (€0/Token). Cloud nur via OpenRouter `:floor`. Skill-Loop. FinOps in LangFuse. |
| **Qualität erhöhen** | Context Bundle + GraphRAG + Unified Search. Guardrails. Human-in-the-Loop. |
| **Skalierbar** | Layered Deployment. Tenant-Isolation. Postgres-Checkpoints. Compose-Profile. |
| **Erweiterbar** | MCP-Gateway. SDK-Contract. Fach-Agenten als SKU-Pakete. Versionierte Skills. |

---

## Was v2 über v1 hinaus leistet

v1 hat die Prinzipien bewiesen. v2 **erzwingt** sie mit genau einem technischen Pfad:

| Konzept | v1 | v2 |
|---------|----|----|
| Datenprodukte | Möglich, umgehbar | Einziger Datenpfad — Contract |
| MCP-Konnektivität | Größtenteils | Erzwungen via SDK |
| Multi-Tenant | Ordnerstruktur | Runtime-Isolation |
| Skill-Loop | P1-Baustelle | Von Tag 1 eingebaut |
| Orchestrierung | Eigener Runner | LangGraph State-Machine |
| Monitoring | Spät/optional | LangFuse ab Tag 1 |
| Suche + Modellwahl | Verstreut | Platform-Services |
| Inference | Gemischt | Ollama (Default) + OpenRouter (Cloud) |

---

## Leitprinzipien

**Detail (Regeln · Verboten · Abnahme):** [12-LEITPRINZIPIEN.md](12-LEITPRINZIPIEN.md)

| Nr. | Prinzip                             | Kernregel                                                                    |
| --- | ----------------------------------- | ---------------------------------------------------------------------------- |
| P1  | **Kontextsystem vor Agenten**       | Dispatch liefert Context Bundle (7 Slices); Agent baut kein eigenes RAG      |
| P2  | **Nicht alles speichern**           | Schichtregeln; LLM setzt nie Speicherziel; L1 nur published                  |
| P3  | **Graph vor reinem RAG**            | Beziehungen in G; Search mit Graph/Fusion                                    |
| P4  | **Determinismus in der Hülle**      | Routing, Guardrails, Audit, FinOps = Code; LLM = Facharbeit                  |
| P5  | **MCP als einzige Konnektivität**   | Nur `self.mcp`; Allowlist + Caps + Audit                                     |
| P6  | **Skill-Loop**                      | Erfolg → versionierter Skill → Wiedervorlage im Bundle                       |
| P7  | **State-Machine**                   | LangGraph + Checkpoints; Workflows resumierbar                               |
| P8  | **Agent-Contract**                  | SDK; In/Out = DataProduct; Tenant immer explizit                             |
| P9  | **Alles in die Datenbank**          | Run-Ende: Audit Pflicht + DP/G/… laut Schema                                 |
| P10 | **Platform vor Fach-Agenten**       | Platform-Gate vor jedem Fach-SKU-Deploy                                      |
| P11 | **Unified Search + Memory Gateway** | Eine Suche; eine Inference-Tür mit Persist-Hook                              |
| P12 | **FinOps by Design**                | Default lokal (`sovereign`); Cloud messbar ≥ Audit/LangFuse                  |
| P13 | **Qualität durch Kontext**          | Erst Bundle/Retrieval/Skill, dann Premium-Modell                             |
| P14 | **Ein Stack, alle Tiers**           | Dev→Enterprise gleiche Compose-Architektur                                   |
| P15 | **PGE-Trinity**                     | Planner (LLM) → Gatekeeper (Code) → Executor                                 |
| P16 | **Observer Audit**                  | Lokaler Qualitätscheck nach Antworten; fails open                            |
| P17 | **Hash-Audit**                      | Hash-Chain + signierte Run-Receipts                                          |
| P18 | **Company Brain**                   | SSOT = K+G+L1; Letta ≠ Firmenwahrheit — [09](09-COMPANY-BRAIN.md)            |
| P19 | **Platform-VM first**               | VM+Core = erstes Produkt; Capture → ein Gedächtnis — [11](11-PLATFORM-VM.md) |

---

## Was die Plattform ist

```
┌──────────────────────────────────────────────────────────────┐
│  EBENE 1 — LAGEBILD         (täglich, 80 % der Nutzung)     │
├──────────────────────────────────────────────────────────────┤
│  EBENE 2 — WORKFLOWS        (wöchentlich, 15 %)             │
├──────────────────────────────────────────────────────────────┤
│  EBENE 3 — PLATTFORM        (selten, 5 %)                   │
└──────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  ORCHESTRATOR — OS-Kernel · Unified Search · Model Gateway     │
├──────────────────────────────────────────────────────────────┤
│  WORKFLOW-ENGINE (LangGraph) · SKILL-LOOP · MCP-GATEWAY        │
├──────────────────────────────────────────────────────────────┤
│  DATENSCHICHT: L0 · K · G · L1 · L2/L3 · SK · A               │
├──────────────────────────────────────────────────────────────┤
│  INFERENCE: Ollama (Default) · OpenRouter (Cloud) · LangFuse   │
└──────────────────────────────────────────────────────────────┘
```
