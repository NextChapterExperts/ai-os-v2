# AI-OS v2 — Memory-Konzept (einfach erklärt)

**Stand:** Juli 2026  
**Für:** Menschen, die das System verstehen wollen — ohne Architektur-Jargon  
**Detail-Specs:** [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md) · [ROADMAP.md §12](../ROADMAP.md#12-datenschicht-im-detail) · [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md)

---

## In einem Satz

AI-OS hat **kein einzelnes „Gedächtnis“**, sondern **mehrere Speicher mit klarer Aufgabe**.  
Das **Firmenhirn** (Company Brain) ist die Wahrheit. **Letta** ist das Notizbuch des Assistenten.  
Beides zusammen = stark. Nur eines davon = Second-Brain-Falle.

---

## Das Bild

Stell dir vor, AI-OS ist eine Firma mit **verschiedenen Notizbüchern**:

| Bild | Speicher | Aufgabe |
|------|----------|---------|
| Aktenschrank der Firma | **Company Brain** (K + G + kuratiertes L1) | Offizielle Wahrheit |
| Inhaltsverzeichnis im Aktenschrank | **Knowledge Graph (G)** | Wie hängt was zusammen? |
| Stichwortsuche über freigegebene Akten | **L1 Qdrant** | Was klingt / bedeutet ähnlich? |
| Notizbuch des Assistenten | **Letta L2 / L3** | Was besprachen wir? Was weiß ich über dich? |
| Klebezettel am Monitor | **Working / Tactical Memory** | Nur während dieses einen Auftrags |
| Stempelbuch / Protokoll | **Audit (A)** | Wer hat wann was ausgelöst? |
| Kochbuch „So haben wir’s gelöst“ | **Skills (SK)** | Wiederkehrende Verfahren |

---

## Die Speicher im Überblick (mit Art)

### 1. Working Memory — Kurzzeitgedächtnis des Runs

| | |
|--|--|
| **Aufgabe** | Scratchpad während ein Agent gerade arbeitet |
| **Art** | Flüchtiger **Prozess-State** (RAM / Workflow-Checkpoint in Postgres, nicht „Wissensarchiv“) |
| **Technologie** | LangGraph-State + ggf. Run-Scratchpad im Orchestrator |
| **Lebensdauer** | Nur dieser Auftrag |
| **Darf Firmenwahrheit sein?** | Nein — muss erst destilliert werden |

---

### 2. Tactical Memory — Zwischenstand über mehrere Schritte

| | |
|--|--|
| **Aufgabe** | Zwischenergebnisse in einem Multi-Step-Workflow („Schritt 2 von 5“) |
| **Art** | Flüchtiger bis kurzlebiger **Workflow-State** |
| **Technologie** | LangGraph Checkpoints (Postgres) |
| **Lebensdauer** | Bis Workflow Ende / Abbruch |
| **Darf Firmenwahrheit sein?** | Nein — am Ende Destillation nach P9 |

---

### 3. L2 — Letta Archival (episodisches Gedächtnis)

| | |
|--|--|
| **Aufgabe** | „Worüber haben wir letzte Woche gesprochen?“ — Episoden, Zusammenfassungen |
| **Art** | **Vektor-/Dokumentenspeicher** für Agenten-Erinnerungen (semantisch durchsuchbar) |
| **Technologie** | **Letta** Archival Memory (Postgres hinter Letta) |
| **Lebensdauer** | Dauerhaft (Agent-Runtime) |
| **Darf Firmenwahrheit sein?** | **Nein** — Assistentengedächtnis, nicht Aktenschrank |

---

### 4. L3 — Letta Core (Profil / User-Modell)

| | |
|--|--|
| **Aufgabe** | Stabile Fakten über den Nutzer / das Profil („Peter bevorzugt …“) |
| **Art** | **Strukturierte Memory-Blöcke** (Core Memory) im Agenten-Kontext |
| **Technologie** | **Letta** Core / human-Block u. Ä. |
| **Lebensdauer** | Dauerhaft, gepflegt |
| **Darf Firmenwahrheit sein?** | Nur nach Destillation als `org:Claim` → Graph — nicht roh |

---

### 5. K — Kanonische Dateien (Teil des Company Brain)

| | |
|--|--|
| **Aufgabe** | Was ist **offiziell** freigegeben / abgelegt? (Markdown, PDFs, Registry) |
| **Art** | **Dateisystem** (dokumentenorientiert) |
| **Technologie** | Repo / `content/` · `knowledge/` · Tenant-Ordner |
| **Lebensdauer** | Permanent |
| **Merksatz** | Dateien = Wahrheit zum Nachlesen |

---

### 6. G — Knowledge Graph (Teil des Company Brain)

| | |
|--|--|
| **Aufgabe** | **Beziehungen:** Decision → Meeting → Offering; Blog → Serie → Compliance |
| **Art** | **Graph-Datenbank** (Knoten + Kanten), relational in Postgres |
| **Technologie** | Postgres-Tabellen `kg_nodes` / `kg_edges` (Upgrade-Pfad: Apache AGE) |
| **Lebensdauer** | Permanent, versioniert |
| **Merksatz** | Graph = Inhaltsverzeichnis + Zusammenhänge — nicht nur „ähnlicher Text“ |

Typen u. a.: `platform:*`, `blog:*`, `email:*`, **`org:*`** (Company Brain: Person, Offering, Decision, Meeting, Policy, Claim …)  
→ [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md)

---

### 7. L1 — Qdrant (kuratierte semantische Suche)

| | |
|--|--|
| **Aufgabe** | „Finde Texte, die **ähnlich klingen / bedeuten**“ |
| **Art** | **Vektordatenbank** (Embeddings) |
| **Technologie** | **Qdrant** |
| **Lebensdauer** | Rolling (z. B. 90 Tage) — nur kuratiert / published |
| **Darf rein?** | Nein: Roh-Chat, Entwürfe, Working-Memory |

---

### 7b. raw-files — Rohdatei-Suche (Übergangslösung, kein Company Brain)

| | |
|--|--|
| **Aufgabe** | „Haben wir an dem Thema nicht schon mal gearbeitet?“ — über rohe Projektdateien (Code, Markdown, PDFs unter `Projekte/active/`) |
| **Art** | **Eigene Qdrant-Collection**, bewusst getrennt von L1 (`content`) |
| **Technologie** | `core/file_ingest_watcher/` (systemd-Service, lokales Embedding via `fastembed`) |
| **Lebensdauer** | Solange Fach-Agenten (Phase 4) Projektarbeit nicht direkt in AI-OS erledigen |
| **Darf Firmenwahrheit sein?** | **Nein** — ungeprüfte Rohdateien, nie mit L1 vermischen |

Grund: Solange echte Projektarbeit noch in Cursor statt in AI-OS
passiert, sieht das Company Brain sonst nichts davon. Details/Ablösepfad:
[ADR 0002](adr/0002-file-ingest-watcher-und-rolle-von-cursor.md).

---

### 8. SK — Skills

| | |
|--|--|
| **Aufgabe** | „Wie haben wir diesen Aufgabentyp zuletzt gelöst?“ |
| **Art** | **Dokumentenstore + Index** (Markdown + Volltext + Vektor) |
| **Technologie** | SQLite/FTS5 + Qdrant (Skill-Store) |
| **Lebensdauer** | Permanent, versioniert (`SUPERSEDES`) |

---

### 9. A — Audit

| | |
|--|--|
| **Aufgabe** | Nachweis: welcher Agent, welcher MCP-Call, welche Kosten |
| **Art** | **Append-only Log / Ledger** (hash-chained) |
| **Technologie** | Postgres `ai_os_log` |
| **Lebensdauer** | Permanent, unveränderlich |

---

## Company Brain vs. Letta (nochmal klar)

```
COMPANY BRAIN (Firmenwahrheit)
  ├── K   Dateien
  ├── G   Knowledge Graph
  └── L1  nur freigegebene Embeddings

AGENT MEMORY (Assistent)
  ├── Working / Tactical   flüchtig
  ├── L2 Letta Archival    Episoden
  └── L3 Letta Core        Profil

Brücke (nur über Plattform):
  L3-Curator → OrgClaim DataProduct → Commit → G
```

**Second Brain (vermeiden):** Jeder sammelt Markdown + schöner Graph, Agenten raten über Vektoren.  
**Company Brain (Ziel):** Eine SSOT; Mitarbeiter, Agenten, Dashboards greifen **gleich** zu.

---

## Die vier Speicherfragen

| Frage | Antwort aus … | Art |
|--------|----------------|-----|
| Was ist **offiziell**? | K + G | Dateien + Graph |
| Was **klingt ähnlich**? | L1 | Vektoren |
| Was war in der **Session**? | Letta L2/L3 | Agent-Memory |
| **Wer** hat wann was getan? | A | Audit-Log |

---

## Wie kommt Wissen rein? (ohne Bypass)

```
Agent arbeitet
  → darf die Außenwelt nur über MCP anfassen
  → liefert ein typisiertes Datenprodukt (Formular)
  → Plattform speichert deterministisch (G + A, ggf. K/L1)
```

| Aktion | Erlaubt |
|--------|---------|
| Graph **lesen** | MCP `kg` (search / traverse / resolve) |
| Graph **schreiben** | Nur als DataProduct → DP-Commit (nicht frei upserten) |
| Letta füllen | Memory-Hooks / Curators — nicht = Firmenwahrheit setzen |

---

## Drei Betriebsregeln (wichtig)

Damit das Konzept im Alltag nicht „voll und falsch“ wird:

### 1. Query-Router — nicht überall suchen

Vor der Suche entscheidet die Plattform (Code, kein LLM):  
*Welche Schicht ist für diese Frage zuständig?*

| Frage-Typ | Wohin |
|-----------|--------|
| „Was **gilt**?“ (Decision, Policy, Offering) | **nur** Graph (+ Datei) |
| „Was ist **ähnlich** / Inhalt?“ | L1 (+ ggf. Graph) |
| „Was haben wir **besprochen**?“ | **nur** Letta |
| „**Wie** haben wir das gelöst?“ | Skills |

### 2. Claims sind Vorschläge — nicht Wahrheit

Fakten aus Letta werden erst nach **Confidence**, **Dedup** und bei heiklen Links (`supports` auf Offering/Decision) nach **Human-Gate** zum Graph-Claim.

### 3. Ein Commit = Datei + Knoten + Kanten

Bei Entscheidungen, Policies, Offerings: entweder **alles** landet (Datei in K + Eintrag in G) oder **nichts**. Kein Knoten ohne Datei, keine Datei ohne Knoten.

Details: [09-COMPANY-BRAIN.md §12](09-COMPANY-BRAIN.md#12-betriebsoptimierungen-verbindlich)

---

## Mini-Beispiel

Du fragst: *„Welche Entscheidung gilt für Consulting mit PBD?“*

1. **G** sagt: Decision X → `about` Offering Consulting → Organization PBD, Status `active`  
2. **K** liefert den Entscheidungstext als Datei  
3. **L1** kann ergänzende Blog-/Research-Absätze finden  
4. **Letta** weiß höchstens: „Letzte Woche hattest du das schon mal angesprochen“

Ohne Graph (nur Vektoren) bekommst du **ähnliche Texte**.  
Mit Company Brain bekommst du **die geltende Entscheidung**.

---

## Was du dir merken solltest

1. **Mehrere Speicher, eine Wahrheit** — die Wahrheit sitzt in K+G, nicht in Letta allein.  
2. **Art beachten** — Datei ≠ Graph ≠ Vektor ≠ Agent-Memory ≠ Audit.  
3. **Nicht alles speichern** — Rohzeug bleibt draußen (P2).  
4. **Agenten sind Vertragsarbeiter** — MCP rein, Datenprodukt raus.  
5. **Richtig suchen** — Query-Router statt „alles befragen“.  
6. **Atomar speichern** — kanonische Dinge: Datei und Graph zusammen oder gar nicht.

---

## Weiterlesen

| Dokument | Inhalt |
|----------|--------|
| [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md) | Ontologie `org:*`, Gates, MCP-Caps |
| [03-DATENPRODUKTE.md](03-DATENPRODUKTE.md) | Welche Formulare (DPs) es gibt |
| [11-PLATFORM-VM.md](11-PLATFORM-VM.md) | VM, Memory Gateway, Chat Capture (Gemini …) |
| [ROADMAP.md §12.4](../ROADMAP.md#124-company-brain--wissensmanagement) | Verbindliche Bauanleitung |
| [14-KONTEXT.md](14-KONTEXT.md) | Was bei Lagebild-Fragen ans LLM geht (Retrieval, Prompt, Bundle) |
| [02-AGENT-SDK.md](02-AGENT-SDK.md) | Wie ein Agent speicherkonform arbeitet |
| [ADR 0002](adr/0002-file-ingest-watcher-und-rolle-von-cursor.md) | File-Ingest-Watcher, `raw-files`, Cursor vs. Fach-Agenten |
