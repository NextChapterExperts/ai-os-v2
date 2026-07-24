# ADR 0002 — File-Ingest-Watcher als Brücke, bis Fach-Agenten Projektarbeit übernehmen

**Status:** angenommen · **Datum:** 2026-07-24 · **Autor:** Peter / NCE
**Verwandt:** [09-COMPANY-BRAIN.md](../09-COMPANY-BRAIN.md) ·
[10-MEMORY-EINFACH.md](../10-MEMORY-EINFACH.md) ·
[13-IST-STAND.md](../13-IST-STAND.md) · [ROADMAP.md](../../ROADMAP.md) ·
[0001-customer-data-isolation.md](0001-customer-data-isolation.md)

---

## Kontext

AI-OS ist als Plattform gedacht, auf der man mit Agenten die komplette
Projektarbeit macht ("auf das OS drauf gehen und da drin mit Agenten
arbeiten"). Faktisch läuft die eigentliche Projektarbeit (RedRays,
WAQAM, SAP-Consultant-Package, …) heute aber in **Cursor**: dort wird
im Dialog mit einer KI entwickelt, geschrieben, recherchiert — Cursor
übernimmt gerade die Rolle, die eigentlich Fach-Agenten in AI-OS haben
sollten.

Das ist kein Versehen, sondern der aktuelle Bauzustand
([13-IST-STAND.md](../13-IST-STAND.md)):

| Phase | Thema | Status |
|---|---|---|
| 1b | Chat Capture | teilweise (Cursor → SQLite; Gemini/Antigravity/UI fehlen) |
| 2 | Platform-Agenten + Platform-Gate | offen |
| 3 | Agent-SDK | offen |
| 4 | **Fach-Agenten** (würden Projektarbeit übernehmen) | **gesperrt** (vor Gate) |

Solange Fach-Agenten gesperrt sind, gibt es strukturell nichts in AI-OS,
das die Rolle "im Dialog mit KI ein Projekt bearbeiten" übernehmen
könnte — deshalb ist Cursor dafür im Einsatz. Damit ergeben sich drei
Rollen, nicht zwei:

| Rolle | Heute | Ziel |
|---|---|---|
| A. AI-OS selbst bauen (Code) | Cursor | bleibt Cursor (normale Softwareentwicklung) |
| B. NCE-Projektarbeit (Inhalte, Recherche, Deliverables) | Cursor | **Fach-Agenten in AI-OS** (Phase 4) |
| C. Gedächtnis führen (was wurde wann gemacht) | nur Chat-Capture, lückenhaft | entsteht automatisch aus B, sobald B in AI-OS passiert |

Bis Rolle B nach AI-OS wandert, entstehen echte Arbeitsergebnisse
weiterhin als **rohe Dateien** unter `Projekte/active/<slug>/` — Code,
Markdown, PDFs — ohne dass AI-OS sie sieht. Chat-Capture
(`core/capture/cursor-job.mjs`) erfasst nur die Dialoge, nicht die
Dateien selbst. Fragen wie "haben wir an dem Thema nicht schon mal
gearbeitet?" lassen sich damit nicht zuverlässig beantworten.

## Entscheidung

Zwei Maßnahmen als **Übergangslösung (Horizont 1)**, explizit befristet
bis Fach-Agenten (Phase 4) stehen:

**1. Eigenes Git-Repo für `Projekte/`**
`/home/peter/Projekte/` ist jetzt ein eigenes Git-Repo (getrennt von
`1100-AI-OS-V2/`), das `active/`, `ops/` und die Obsidian-Vault-Dateien
versioniert. Projekte mit eigenem Git-Repo
(`sap-consultant-package`, `waqam-doku`, `waqamboard`) werden bewusst
**nicht** als eingebettetes Repo mitgezogen (`.gitignore`) — sie haben
ihre eigene Historie. `archive/` ist vorerst ausgeschlossen (u. a.
Altlasten/Secrets in `archive/ai-os-v1`).

**2. File-Ingest-Watcher** (`core/file_ingest_watcher/`)
Python-Service, läuft als systemd-User-Service dauerhaft:

- Scannt `Projekte/active/**` alle 5 Minuten (`SCAN_INTERVAL_SEC`),
  erkennt neue/geänderte/gelöschte Dateien per SHA-256-Hash-Diff
  (State-DB: SQLite unter `/opt/ai-os/ingest/file_watcher_state.db`).
- Extrahiert Text (Markdown inkl. Frontmatter, Code, PDF via `pypdf`).
- Chunked (1500 Zeichen, 200 Overlap) und embedded lokal via
  `fastembed` (Modell `paraphrase-multilingual-MiniLM-L12-v2`, 384-dim,
  mehrsprachig, läuft CPU-only ohne externe API/Kosten).
- Schreibt in eine **eigene, neue Qdrant-Collection `raw-files`** —
  bewusst getrennt von der kuratierten Company-Brain-Collection
  (`content`). Rohdateien sind ungeprüft und sollen in der späteren
  Unified Search klar als "Rohdatei" markiert werden, nicht mit
  freigegebenem Wissen vermischt werden.
- Stößt vor jedem Scan optional einen Git-Auto-Commit im
  `Projekte`-Repo an (`GIT_SNAPSHOT_ENABLED=true`), damit
  "wie sah das vor 3 Monaten aus" über `git log` beantwortbar wird.

Explizit **kein** Ersatz für den in [09-COMPANY-BRAIN.md](../09-COMPANY-BRAIN.md)
beschriebenen L1/DP-Commit-Weg — `raw-files` ist ein dritter,
zusätzlicher Weg neben Chat-Capture und dem echten Ingest-Agent
(Phase 2, Inbox → DP-Commit), nicht dessen Nachfolger.

## Konsequenzen

**Positiv**

- Schließt die akute Gedächtnislücke (Dateien/PDFs/Code werden jetzt
  durchsuchbar), ohne auf Phase 2–4 warten zu müssen.
- Kein API-Key/Kosten-Abhängigkeit für Embeddings (lokal via
  `fastembed`), passt zur "sovereign zuerst"-Linie des Stacks.
- Git-Historie in `Projekte/` beantwortet zeitliche Fragen unabhängig
  von Qdrant/Chunking.
- Sauber vom kuratierten Company-Brain getrennt (`raw-files` ≠
  `content`) — kein Risiko, dass Rohentwürfe versehentlich als
  freigegebenes Wissen zitiert werden.

**Zu beachten / Trade-offs**

- **Befristet gedacht:** Sobald Fach-Agenten (Phase 4) Projektarbeit
  direkt in AI-OS erledigen, sollte deren Output über den regulären
  DP-Commit-Weg ins Company-Brain fließen — der Watcher wird dann für
  aktive Projektarbeit weniger relevant, bleibt aber nützlich für
  Material, das ohnehin außerhalb entsteht (Kundendokumente, Belege).
  Diese Ablösung ist nicht automatisiert, sondern eine spätere
  bewusste Entscheidung.
- Unified Search (die `raw-files` und `content` gemeinsam durchsuchen
  und unterscheiden soll) ist noch nicht gebaut (Phase 1, siehe
  13-IST-STAND.md) — bis dahin nur direkte Qdrant-Abfragen möglich.
- Kein OCR/Docling, keine Bild-/Office-Formate (`.docx`, `.xlsx`,
  `.pptx`) in diesem MVP — nur Text/Code/Markdown/PDF. Erweiterung
  später möglich.
- `archive/` wird aktuell weder git-versioniert noch vom Watcher
  gescannt — bei Bedarf später gezielt nachziehen (ohne
  `archive/ai-os-v1`, das Secrets enthält).
- Enger Python-`venv` nur für diese Komponente (`core/file_ingest_watcher/.venv`),
  da das Root-`.venv` ohne `pip` gebaut wurde — sollte bei Gelegenheit
  vereinheitlicht werden.

## Alternativen (verworfen)

- **Warten auf Phase 2 (echter Ingest-Agent) und bis dahin nichts
  tun:** verworfen — die Gedächtnislücke besteht schon jetzt aktiv,
  jeden Tag ungenutzte Projektarbeit ist verlorenes Wissen.
- **Rohdateien direkt in die `content`-Collection mischen:** verworfen
  — verwässert die kuratierte Company-Brain-Qualität, widerspricht dem
  L1-Prinzip "nur freigegebenes Wissen" aus 09-COMPANY-BRAIN.md.
- **Cloud-Embedding-API (OpenAI o. ä.) statt lokal:** verworfen für den
  MVP — zusätzliche Kosten/Abhängigkeit für einen Übergangsdienst, der
  ohnehin abgelöst werden soll; lokal via `fastembed` reicht für
  Ähnlichkeitssuche in diesem Umfang.
