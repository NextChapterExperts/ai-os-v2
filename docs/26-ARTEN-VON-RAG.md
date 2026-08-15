# 🔍 VIRKI AI-OS v2 — Arten von RAG & Die Graph-RAG Architektur

> **Status:** Verbindliche Architektur-Spezifikation & Technologie-Einordnung  
> **Verwandte Dokumente:** [25-COMPANY-BRAIN-MEMORY-MAPPING.md](25-COMPANY-BRAIN-MEMORY-MAPPING.md) · [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md) · [10-MEMORY-EINFACH.md](10-MEMORY-EINFACH.md) · [14-KONTEXT.md](14-KONTEXT.md)

---

## 🎯 1. Die Taxonomie der 4 RAG-Evolutionsstufen

Retrieval-Augmented Generation (RAG) hat sich von primitiven Vektor-Lookups zu hochkomplexen Wissensarchitekturen entwickelt. VIRKI setzt sich bewusst von trivialen Ansätzen ab.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   DIE 4 EVOLUTIONSSTUFEN VON RAG                                 │
├───────────────────────┬───────────────────────────────────┬──────────────────────────────────────┤
│ RAG-ARCHITEKTUR       │ KERNMECHANISMUS                   │ SCHWÄCHEN & EINSCHRÄNKUNGEN          │
├───────────────────────┼───────────────────────────────────┼──────────────────────────────────────┤
│ 1. Natives /          │ Text in Chunks zerlegen ──►       │ ❌ Blindes Retrieval. Keine Kanten,  │
│    Einfaches RAG      │ Vektor-DB ──► Cosine-Suche ──►    │ keine Hierarchien, hohe Anfälligkeit │
│    (Naive RAG)        │ Top-K Chunks in LLM-Prompt.       │ für veraltete/widersprüchliche Daten.│
├───────────────────────┼───────────────────────────────────┼──────────────────────────────────────┤
│ 2. Advanced RAG       │ Vektorsuche + Vor-/Nachbereitung: │ ❌ Erkennt zwar thematisch ähnliche  │
│                       │ Query Rewriting, Hybrid Search    │ Texte besser, versteht aber keine    │
│                       │ (BM25 + Dense) & Re-Ranking.      │ mehrstufigen Beziehungsstrukturen.   │
├───────────────────────┼───────────────────────────────────┼──────────────────────────────────────┤
│ 3. Modulares RAG      │ Flexible Pipeline: Dynamische     │ ❌ Weiterhin stochastisch gesteuert; │
│                       │ Routing-Module, Query Expansion,  │ hohe Token-Kosten durch paralleles   │
│                       │ Self-Correction Loops (CRAG).     │ Abfragen aller Module ohne Schranken.│
├───────────────────────┼───────────────────────────────────┼──────────────────────────────────────┤
│ 4. VIRKI Hybrid       │ Deterministischer Query-Router +  │ ✅ 100% Beziehungspräzision im Graph │
│    Graph-RAG          │ Knowledge Graph ($G$) Traversing  │ kombiniert mit semantischer Breite   │
│    (State of the Art) │ + kuratierter Vektor-Index ($L1$) │ im Vektor-Index. Mathematisch        │
│                       │ + Unified Answer Synthesizer.     │ minimierte Halluzinationsrate.       │
└───────────────────────┴───────────────────────────────────┴──────────────────────────────────────┘
```

---

## 🏗️ 2. Die 4-Stufen-Retrieval-Pipeline in VIRKI

Das Retrieval in VIRKI AI-OS v2 folgt einer strikt geordneten, hybrid-deterministischen Pipeline:

```text
                              Benutzer-Anfrage
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. PRE-RETRIEVAL: Deterministischer Query-Router (core/orchestrator/query_router.py)│
│    - Code-basiert (Kein LLM-Call, 0 Token-Kosten, 0 ms Latenz)              │
│    - Erstellt strikten SearchPlan: Welche Speicher dürfen befragt werden?   │
│    - Schließt bei Geltungsfragen alte Chat-Episoden (S2) strikt aus.        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                       ┌───────────────┴───────────────┐
                       ▼                               ▼
┌─────────────────────────────────────────────┐ ┌─────────────────────────────┐
│ 2. STRUKTURELLES GRAPH RETRIEVAL (G)        │ │ 3. SEMANTISCHES VEKTOR-RAG  │
│    (core/orchestrator/kg_search.py)         │ │    (L1 / Qdrant & fastembed)│
│    • 1-Hop & 2-Hop Graph-Traversierung      │ │    • Collection: content    │
│    • Kanten: applies_to, documents,         │ │    • Collection: raw-files  │
│      supports, decided_in, supersedes       │ │    • Multilingual MiniLM    │
│    • Exakte Fakten, Personen, Verträge      │ │    • Semantische Ähnlichkeit│
└──────────────────────┬──────────────────────┘ └──────────────┬──────────────┘
                       │                                       │
                       └───────────────┬───────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. POST-RETRIEVAL: Unified Search Fusion & LLM-Synthese                     │
│    (core/orchestrator/handlers/unified_search.py)                           │
│    - Fusioniert Graph-Pfade mit relevanten Vektor-Textabschnitten           │
│    - LLM Answer Synthese (kind: "ask") für präzise Antworten                │
│    - Lückenloser Quellennachweis (Citations & Node-IDs)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 💡 3. Praxis-Vergleich: Warum Naives RAG scheitert und Graph-RAG gewinnt

### Die typische Enterprise-Anfrage:
> *„Welche Reisekosten-Regelung gilt für das Projekt von Kunde Müller und wer hat das entschieden?“*

### Szenario A: Naives RAG (Vector-Only)
1. Die Vektorsuche sucht nach Chunks mit den Wörtern *„Reisekosten“*, *„Müller“*, *„Projekt“*.
2. Sie findet:
   - Eine alte E-Mail von 2023, in der jemand über ein Reisekosten-Problem klagte.
   - Einen Entwurf für einen Kunden namens „Müller & Söhne“ (ein anderer Kunde).
   - Eine veraltete Reiserichtlinie von 2024.
3. Das LLM generiert daraus eine plausibel klingende, aber **komplett falsche Antwort** (Halluzination).

### Szenario B: VIRKI Advanced Graph-RAG
1. **Query-Router:** Erkennt eine Geltungs-/Regelfrage $\rightarrow$ `SearchPlan(use_g=True, use_k_resolve=True, use_l1=False, use_letta=False)`. Der persönliche Chat-Speicher ($\mathcal{S}_2$) wird gesperrt.
2. **Graph-Navigation:**
   - Findet den Mandanten-Knoten `org:Organization (Müller GmbH)`.
   - Folgt der Kante `has_engagement` $\rightarrow$ `org:Engagement (Projekt ERP-Rollout)`.
   - Folgt der Kante `governed_by` $\rightarrow$ `org:Policy (Reiserichtlinie 2026)`.
   - Folgt der Kante `decided_in` $\rightarrow$ `org:Decision (Vorstandsbeschluss #42 vom 12.01.2026)` $\rightarrow$ `decided_by` $\rightarrow$ `org:Person (Dr. Schmidt)`.
3. **Kanonische Auflösung ($K$):** Lädt den exakten Paragraphen aus der Datei `docs/policies/Reisekosten_2026.md`.
4. **Ergebnis:**  
   > *„Für das Projekt ERP-Rollout bei der Müller GmbH gilt die Reiserichtlinie 2026 (max. 150 €/Nacht). Dies wurde am 12.01.2026 durch Dr. Schmidt (Vorstandsbeschluss #42) festgelegt. [Quelle: Decision_42.md]“*

---

## 📂 4. Relevante Dateien im Quellcode

| Komponente | Datei im Repository | Funktion |
|---|---|---|
| **Query-Router** | [`core/orchestrator/query_router.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/orchestrator/query_router.py) | Deterministischer Pre-Retrieval Router ($\mathcal{R}(\text{Intent})$). |
| **Graph-Retrieval** | [`core/orchestrator/kg_search.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/orchestrator/kg_search.py) | Traversierung von Knoten und 1-Hop/2-Hop-Kanten in Postgres. |
| **Vektor-Index** | [`core/ingest_agent/doc_ingest.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/ingest_agent/doc_ingest.py) | FastEmbed-Indizierung in Qdrant Collections `content` & `raw-files`. |
| **Unified Fusion** | [`core/orchestrator/handlers/unified_search.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/orchestrator/handlers/unified_search.py) | Fusioniert Graph-Ergebnisse mit Text-Chunks & generiert Synthese. |
| **Commit Gateway** | [`core/orchestrator/dp_service.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/orchestrator/dp_service.py) | Schreibt neue Graph-Knoten und Kanten atomar bei DataProduct-Commits. |

---

## 🧪 5. Automatisierte Tests

Die Funktionsweise des Graph-Retrievals und des Query-Routers ist mit automatisierten Pytests abgesichert:

```bash
.venv/bin/pytest tests/test_query_router_search.py tests/test_dataproducts_graph.py
```
*(17 Tests prüfen exakt diese Intent-Klassen, Kantenauflösungen und Tokenisierungen).*
