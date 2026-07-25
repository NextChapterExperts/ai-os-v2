# AI-OS v2 — Kontext verstehen (Lagebild → LLM)

**Stand:** Juli 2026  
**Für:** Menschen, die nachvollziehen wollen, *was* bei einer Lagebild-Frage passiert — und *was* ans lokale Modell geht  
**Verwandt:** [10-MEMORY-EINFACH.md](10-MEMORY-EINFACH.md) (Speicher) · [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md) (Wahrheit) · [12-LEITPRINZIPIEN.md](12-LEITPRINZIPIEN.md) (P1 Kontextsystem) · [ROADMAP.md §6.8](../ROADMAP.md#68-lagebild--federierter-ask--llm-kontext-2026-07-25)

---

## In einem Satz

Bei jeder Frage im **Lagebild** durchsucht AI-OS zuerst verschiedene Gedächtnis-Speicher, baut daraus einen **Prompt** für das lokale Modell (Ollama) — und speichert diesen Prompt pro Aufruf, damit du ihn unter **„LLM-Kontext anzeigen“** nachlesen kannst.

---

## Das Bild: drei Schichten

Stell dir eine Frage wie eine Anfrage an einen Assistenten mit Bibliothek vor:

```text
Du stellst eine Frage im Lagebild
           │
           ▼
  ① Orchestrator-Rahmen     „Wer bin ich, welche Policies, welche Engagements?“
           │
           ▼
  ② Retrieval               „Was finden wir in Graph, L1, Dateien, Chat?“
           │
           ▼
  ③ LLM-Prompt              „Frage + ausgewählte Textstücke → Ollama“
           │
           ▼
  Antwort (Zusammenfassung)
```

| Schicht | Name | Analogie |
|---------|------|----------|
| ① | **Orchestrator Context Bundle** | Briefkopf der Firma: Policies, Tenant, aktive Engagements |
| ② | **Retrieval** | Bibliothekar holt passende Akten und Notizen |
| ③ | **LLM-Prompt** | Das Blatt Papier, das du dem Modell wirklich vorlegst |

**Wichtig:** Das Modell sieht **nur Schicht ③** (plus System-Anweisung). Es hat keinen direkten Zugriff auf Qdrant, Letta oder Dateien auf der Platte.

---

## Was passiert bei „Wie ist der Stand bei RedRays?“

1. **Intent-Routing** — Orchestrator erkennt: das ist eine Gedächtnis-/Stand-Frage → Handler `memory_ask`.
2. **Federated-Entscheidung** — Keywords wie „Stand bei“, Projektname `redrays` oder „ROADMAP“ → **federated = ja**. Dann wird nicht nur Chat-Gedächtnis (Letta) durchsucht, sondern auch **Graph + kuratiertes L1**.
3. **Unified Search** — Suchanfrage wird angereichert (z. B. `… ROADMAP Engagement org:KnowledgeAsset`).
4. **Chunks sammeln** — Treffer aus Graph, L1, ggf. raw-files und wenig Episodik; sortiert nach Priorität (Graph/kuratiert vor Chat).
5. **Prompt bauen** — System-Text + User-Text mit Frage und max. ~5.500 Zeichen Kontext.
6. **Ollama** — Antwort über Memory Gateway (eine Tür, Audit-Hook).
7. **Speichern** — vollständiger Kontext unter `/context/{runId}` ablegbar.

Ohne federated (z. B. „Was haben wir gestern besprochen?“) kommt fast nur **episodisches** Gedächtnis (Letta/SQLite) ins Spiel.

---

## Die Kontext-Seite (`/context/{runId}`)

Nach jeder Lagebild-Antwort erscheint der Link **„LLM-Kontext anzeigen“**. Die Seite ist in fünf Bereiche gegliedert:

### 1. Routing & Modell

Steuerungsinfo **für diesen einen Aufruf**:

| Feld | Bedeutung |
|------|-----------|
| **Handler** | Welcher Code antwortet (`memory_ask` = Lagebild-Frage) |
| **Intent** | Wie der Orchestrator die Eingabe klassifiziert hat |
| **Modell** | Welches LLM (aktuell Ollama, z. B. `qwen3.6-64k`) |
| **Tier** | `local` heute — später `cloud` oder `agent` |
| **Memory / Federated** | Nur Chat, oder auch Company Brain? |
| **Tenant** | Organisation (z. B. `nextchapter`) |

### 2. Retrieval

Alles, was **vor** dem LLM-Call aus dem Gedächtnis geholt wurde:

- **Frage** — deine Originalfrage  
- **Federated Query** — oft erweiterte Suchanfrage  
- **Chunks** — einzelne Textstücke mit Quelle, Titel, Vorschau  

#### Woher kommen die Chunks?

| `source` / Typ | Speicher | Was steckt drin? | Vertrauenswürdigkeit |
|----------------|----------|------------------|----------------------|
| **graph** | Knowledge Graph (G) | Engagements, KnowledgeAssets, Claims, Beziehungen | Hoch — kuratiert, SSOT |
| **curated** | L1 Qdrant `content` | Freigegebene Dokument-Chunks (ROADMAP, Seeds) | Hoch — published L1 |
| **raw-file** | L1 Qdrant `raw-files` | Rohe Projektdateien (README, Code, …) | Mittel — noch nicht kuratiert |
| **episodic** | Letta L2 + SQLite | Chat-Verläufe, Tagesdigests | Niedrig für Firmenwahrheit — „was besprochen wurde“ |

Nicht alle gefundenen Chunks landen im Prompt — es gilt ein Zeichenlimit; die relevantesten (Graph/kuratiert zuerst) gewinnen.

### 3. System-Prompt

Die **Regeln für das Modell** — kein Wissen, sondern Anweisung:

- Antworte auf Deutsch, nur aus dem Kontext  
- Kurz: max. 5 Bulletpoints  
- Bei Projektstand: ROADMAP und Graph haben Vorrang vor Chat-Episoden  

### 4. User-Prompt

Der **tatsächliche Input ans LLM** — das Wichtigste zum Prüfen:

```text
Frage: Wie ist der Stand bei RedRays?

Gedächtnis-Kontext:
[graph] org:KnowledgeAsset: RedRays ROADMAP
… Text aus der ROADMAP …
---
[graph] org:Engagement: RedRays …
…
```

Genau dieser Text (plus System-Prompt) ist alles, was Ollama „weiß“.

### 5. Orchestrator Context Bundle

Der **größere Rahmen**, den der Orchestrator bei **jedem** Dispatch mitliefert — auch wenn nicht alles ins LLM fließt:

| Slice | Inhalt |
|-------|--------|
| **system** | Tenant, Compute-Modus (`sovereign`), Policies |
| **domain** | Offerings & aktive Engagements aus dem Brain |
| **task** | Intent, Run-ID, Working Memory (Notizen dieses Laufs) |
| **retrieval** | Platzhalter — Handler füllt Retrieval selbst |
| **episodic** | Verweis auf Letta / Run-Destillation |
| **guardrail** | z. B. `sovereign_default`, Quellen on demand |
| **skill** | Noch leer — später wiederkehrende Verfahren |

---

## Zwei Kontext-Ebenen — der Unterschied

| | Context Bundle | LLM-Prompt (System + User) |
|--|----------------|----------------------------|
| **Wann gebaut?** | Zu Beginn jedes Dispatch | Im Handler `memory_ask`, nach Retrieval |
| **Zweck** | Rahmen für alle Agenten (P1) | Konkrete Modell-Eingabe |
| **Enthält Firmenwissen?** | Metadaten (Engagement-Liste), nicht Volltexte | Ja — ausgewählte Chunk-Texte |
| **Heute im Lagebild** | Wird mitgespeichert, selten direkt ans LLM | **Das entscheidet die Antwort** |
| **Später** | Filter/Redaction vor Cloud-Modellen | Pro Agent/Tier steuerbar |

**Merksatz:** Bundle = *Büroausstattung und Regeln*. User-Prompt = *die Akten auf dem Tisch vor dem Modell*.

---

## Wo liegt welches Wissen? (Gesamtbild)

```text
Company Brain — langfristige Wahrheit (P18)
├── Knowledge Graph (G)     Engagements, ROADMAP-Assets, Claims
├── L1 Qdrant (content)     kuratierte Chunks (Knowledge Assets)
└── raw-files               alle Projektdateien (File-Ingest-Watcher)

Episodisch — „was besprochen wurde“
├── Letta L2                Chat-Zusammenfassungen, Tagesdigests
└── SQLite memory.db        Cursor-Chat-Chunks

Run-spezifisch — nur dieser Aufruf
├── Working Memory          Scratchpad während des Laufs
└── Run-Context-Store       gespeicherter Prompt (/context/{runId})
```

Details zu den Speichern: [10-MEMORY-EINFACH.md](10-MEMORY-EINFACH.md).

---

## Technik (kurz)

| Thema | Pfad / Endpoint |
|-------|-----------------|
| Handler | `core/orchestrator/handlers/memory_ask.py` |
| Context Bundle | `core/orchestrator/context_resolution.py` |
| Run speichern | `core/orchestrator/run_context_store.py` |
| API abrufen | `GET /v1/runs/{run_id}/context` |
| Persistenz | `AIOS_RUN_CONTEXT_DIR` → Default `/opt/ai-os/memory/state/run-context/{runId}.json` |
| Console | Link im Lagebild → `/context/{runId}` |

Der Orchestrator entfernt `llmContext` aus der Dispatch-Antwort (kein riesiges JSON im Browser) — nur `runId` und der Link. Vollständiger Inhalt liegt serverseitig.

---

## Warum das für später wichtig ist (Fachagenten & Cloud)

Wenn öffentliche Modelle oder spezialisierte Fachagenten dazukommen, braucht AI-OS **nachvollziehbare Kontrolle**:

1. **Was wurde gesucht?** → Retrieval (auditierbar)  
2. **Was ging ans Modell?** → System + User-Prompt (reproduzierbar)  
3. **Welches Modell / welcher Tier?** → `routing.modelTier` (`local` → `cloud` / `agent`)  
4. **Welche Policies galten?** → Context Bundle (`pii_local_default`, `sovereign_default`)  

Geplante Regeln (noch nicht voll implementiert):

- Episodisches Chat-Gedächtnis **nicht** an Cloud ohne Redaction  
- ROADMAP/Graph **dürfen** an Fachagenten für Projektstand  
- Context Bundle dient als **Filter-Schicht** vor dem Prompt-Bau  

Leitprinzip P1: *Kontextsystem vor Agenten* — kein Agent baut sein RAG allein; der Orchestrator liefert den Rahmen.  
Leitprinzip P13: *Qualität durch Kontext* — erst Bundle/Retrieval, dann Premium-Modell.

---

## Häufige Fragen

**Warum antwortet das Modell manchmal „keine Informationen“, obwohl ROADMAP existiert?**  
Dann war vermutlich **kein federated Retrieval** aktiv (nur Letta) oder die ROADMAP war noch nicht als Knowledge Asset ingestiert. Kontext-Seite prüfen: stehen `graph`/`curated`-Chunks im User-Prompt?

**Was ist der Unterschied zu Unified Search (`/search`)?**  
Unified Search **listet Treffer**. Lagebild `memory_ask` **sucht + fasst zusammen** via LLM. Beides nutzt ähnliche Quellen; der Ask-Pfad baut zusätzlich den Prompt.

**Kann ich alte Kontexte wiederfinden?**  
Ja, solange die JSON-Datei im Run-Context-Store liegt — URL `/context/{runId}`. Die Run-ID steht implizit im Link nach jeder Antwort.

---

## Siehe auch

- [05-CONSOLE-IA.md](05-CONSOLE-IA.md) — Lagebild als Ebene 1 (80 %-Nutzung)  
- [13-IST-STAND.md](13-IST-STAND.md) — was heute wirklich läuft  
- [ROADMAP.md §6.8](../ROADMAP.md#68-lagebild--federierter-ask--llm-kontext-2026-07-25) — technische Spezifikation
