# 🧠 VIRKI AI-OS v2 — Das 5-Schichten-Memory-Modell (Referenz & Code-Mapping)

> **Status:** Verbindliche Architektur-Dokumentation & Code-Übersicht  
> **Wissenschaftliche Grundlage:** Formal Research Paper & RFC [`company_brain_formal_memory_model_rfc.md`](file:///home/peter/Projekte/active/papers/company_brain_memory_model/de/company_brain_formal_memory_model_rfc.md)  
> **Verwandte Dokumente:** [26-ARTEN-VON-RAG.md](26-ARTEN-VON-RAG.md) (RAG-Taxonomie & Graph-RAG) · [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md) · [10-MEMORY-EINFACH.md](10-MEMORY-EINFACH.md) · [12-LEITPRINZIPIEN.md](12-LEITPRINZIPIEN.md) · [03-DATENPRODUKTE.md](03-DATENPRODUKTE.md)

---

## 🎯 1. Auf einen Blick: Warum dieses Modell existiert

In normalen KI-Systemen führt unkontrolliertes Speichern zum **"Chat-Chaos" (Epistemic Corruption)**: Wenn ein Mitarbeiter im Chat scherzt oder ungenaue Zahlen nennt, speichert eine naive KI das als Fakt ab und halluziniert später falsche Firmenbeschlüsse.

Das **Company Brain Memory Model** löst das durch **zwei getrennte Welten**:
1. **Das Notizbuch des Assistenten (Was wir besprechen / Vorlieben)** $\rightarrow$ Flüchtig & Niedrige Autorität.
2. **Der Aktenschrank der Firma (Verträge, Beschlüsse, Preise, Richtlinien)** $\rightarrow$ Nur freigegebene Fakten (Single Source of Truth).

---

## 🗺️ 2. Die 5 Speicherzustände ($\mathcal{S}_1$ bis $\mathcal{S}_5$) — Mapping auf den Code

Hier ist die vollständige Übersicht, welcher Zustand aus dem Paper welcher Datei im Repository entspricht:

| Zustand im Paper | Bezeichnung im Paper | Umgangssprachliches Bild | Reale Datei(en) im Codebase | Aufgabe im System |
|---|---|---|---|---|
| **$\mathcal{S}_1$ ($\mathcal{S}_{\text{transient}}$)** | *Transient Operational State* | **Der Klebezettel am Monitor** (flüchtig) | [`core/memory/working_memory.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/memory/working_memory.py)<br>[`core/memory/tactical_memory.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/memory/tactical_memory.py) | Hält Denkpfade, Zwischenrechnungen und Zwischenschritte (z. B. Schritt 2 von 5). Wird nach dem Auftrag verworfen. |
| **$\mathcal{S}_2$ ($\mathcal{S}_{\text{episodic}}$)** | *Episodic Conversation State* | **Das persönliche Tagebuch des Assistenten** | [`core/memory/l1_curator.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/memory/l1_curator.py)<br>[`core/memory/l2_curator.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/memory/l2_curator.py)<br>[`core/memory_gateway/letta_client.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/memory_gateway/letta_client.py) | Speichert Chat-Verläufe der letzten Tage und 24h-Tageszusammenfassungen („Was besprachen wir gestern?“). Keine Firmenentscheidung! |
| **$\mathcal{S}_3$ ($\mathcal{S}_{\text{canonical}}$)** | *Canonical Ground Truth State* (Company Brain) | **Der offizielle Aktenschrank der Firma** | **$K$ (Markdown):** [`doc_ingest.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/ingest_agent/doc_ingest.py)<br>**$G$ (Graph):** [`dp_service.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/orchestrator/dp_service.py)<br>**$L1$ (Vektor):** [`unified_search.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/orchestrator/handlers/unified_search.py) | **DAS HERZSTÜCK:** Unumstößliche Wahrheit (Verträge, Richtlinien, Preise). Schreibzugriff **NUR** als typisiertes Datenprodukt via `POST /v1/dataproduct/commit`. |
| **$\mathcal{S}_4$ ($\mathcal{S}_{\text{procedural}}$)** | *Procedural Capability State* | **Das Firmen-Kochbuch („Wie wir Aufgaben lösen“)** | [`core/memory/l3_curator.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/memory/l3_curator.py)<br>[`core/orchestrator/dataproducts.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/orchestrator/dataproducts.py) | Speichert wiederverwendbare Fähigkeiten & Workflows (*Skills*), wenn ein Ablauf mehrfach erfolgreich gelöst wurde. |
| **$\mathcal{S}_5$ ($\mathcal{S}_{\text{audit}}$)** | *Immutable Audit Ledger State* | **Das notarielle Stempelbuch** | [`core/memory_gateway/audit.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/memory_gateway/audit.py)<br>[`core/orchestrator/dp_service.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/orchestrator/dp_service.py) | Unveränderliches Log mit kryptografischer SHA-256 Hash-Kette. Weist lückenlos nach: Wer hat was wann genehmigt und ausgeführt? |

---

## 🗣️ 3. Umgangssprachliche Erklärung: Was passiert in der Praxis?

Um den Überblick im Alltag nicht zu verlieren, hier die 3 wichtigsten Abläufe in einfacher Sprache:

### 1. Wie ein Gedanke zur Firmenwahrheit wird (Das Memory Flywheel)
1. **Der Nutzer chattet mit der KI:**  
   *„Wir sollten den Stundensatz für Kunde Müller auf 180 € erhöhen.“*  
   $\rightarrow$ Das landet zunächst nur auf dem **Klebezettel ($\mathcal{S}_1$)** und im **Tagebuch ($\mathcal{S}_2$)**. Für den Rest der Firma gilt weiterhin der alte Stundensatz!
2. **Die automatische Kurierung (Nachts / Wöchentlich):**  
   [`l2_curator.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/memory/l2_curator.py) fasst den Tag zusammen. [`l3_curator.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/memory/l3_curator.py) prüft: *Ist das ein Fakt? (Confidence $\ge 0.7$, Dedup $\ge 0.95$)*.
3. **Die Validierungs-Schranke (Human-in-the-Loop):**  
   Weil es eine Preisentscheidung betrifft, stoppt das System und fragt den Chef: *„Möchtest du den Stundensatz von 180 € für Müller offiziell festlegen?“*
4. **Der atomare Commit ($\mathcal{S}_3$ & $\mathcal{S}_5$):**  
   Klickt der Chef auf *„Ja“*, ruft VIRKI [`dp_service.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/orchestrator/dp_service.py) auf. Der neue Stundensatz wird im **Aktenschrank ($\mathcal{S}_3$)** gespeichert und im **Stempelbuch ($\mathcal{S}_5$)** besiegelt.  
   Ab jetzt rechnen alle Agenten im gesamten Betrieb verlässlich mit 180 €.

---

### 2. Wie der Query-Router Halluzinationen verhindert
Bisherige RAG-Systeme suchen bei jeder Frage blind in allen Texten gleichzeitig. VIRKI macht das schlauer über den **deterministischen Query-Router** ([`query_router.py`](file:///home/peter/Projekte/1100-AI-OS-V2/core/orchestrator/query_router.py)):

- **Frage nach einer Regel:** *„Welche Reisekosten dürfen wir abrechnen?“*  
  $\rightarrow$ Der Router sucht **ausschließlich im Aktenschrank ($\mathcal{S}_3$)**. Das persönliche Tagebuch ($\mathcal{S}_2$) wird ignoriert. Dadurch liest die KI niemals Gerüchte oder alte Chat-Nachrichten, sondern die 100% gültige Richtlinie.
- **Frage nach der Historie:** *„Was haben wir vor 3 Tagen besprochen?“*  
  $\rightarrow$ Der Router sucht **nur im Tagebuch ($\mathcal{S}_2$)**. Der Aktenschrank wird geschont.

---

### 3. Was bedeutet das für externe Agenten (Hermes, n8n, LangGraph)?
Egal, welche Agenten-Engine auf der VIRKI-VM läuft:
- Sie arbeiten als **flüchtige Handwerker in $\mathcal{S}_1$**.
- Sie dürfen **niemals direkt in die Datenbank schreiben**.
- Sie liefern ihr Ergebnis als **typisiertes Datenprodukt** ab. VIRKI übernimmt die Prüfung und speichert es sicher im Company Brain.

---

## 📂 4. Schnellfinder für Entwickler (Wo liegt was im Code?)

```text
core/
├── memory/
│   ├── working_memory.py      ──► S1: Flüchtige Notizen pro Run
│   ├── tactical_memory.py     ──► S1: Multi-Step Task-Zwischenstände
│   ├── l1_curator.py          ──► S2: Live-Deduplizierung von Chunks
│   ├── l2_curator.py          ──► S2: 24h-Tageszusammenfassungen
│   ├── l3_curator.py          ──► S4/S3: Fakten-Extraktion & Claim-Vorschläge
│   └── run_distill.py         ──► CLI-Runner für Destillations-Läufe
│
├── memory_gateway/
│   ├── letta_client.py        ──► S2: Schnittstelle zu Letta Archival Memory
│   ├── audit.py               ──► S5: LLM- & Intent-Audit-Logging
│   └── sqlite_schema.py       ──► Schema für lokale memory.db (FTS5)
│
├── orchestrator/
│   ├── dp_service.py          ──► S3/S5: POST /v1/dataproduct/commit (SSOT-Schreibschranke)
│   ├── query_router.py        ──► Deterministischer Router R(Intent) -> {S_i}
│   ├── dataproducts.py        ──► Pydantic-Definitionen der org:*-Schemas
│   └── handlers/
│       └── unified_search.py  ──► Fusionierte Suche über Graph (G) + Vektor (L1)
│
└── ingest_agent/
    └── doc_ingest.py          ──► S3: Indizierung von kanonischen Markdown-Dokumenten (K)
```

---

## 🧪 5. Wie wird dieses Speichermodell getestet?

Alle 5 Schichten und Übergänge werden durch automatisierte Unit- und E2E-Tests in `tests/` überwacht:

```bash
# Ausführen aller 34 Memory- & Router-Tests:
.venv/bin/pytest tests/test_memory_flywheel_e2e.py \
                 tests/test_query_router_search.py \
                 tests/test_dataproducts_graph.py \
                 tests/test_l1_working_memory.py \
                 tests/test_l2_curator.py \
                 tests/test_l3_curator.py
```
*(Alle 34 Tests laufen in < 1 Sekunde durch und sind zu 100% grün).*
