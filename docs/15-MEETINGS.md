# AI-OS v2 — Meeting-Inbox

**Stand:** Juli 2026  
**UI:** Console `/meetings` · **API:** `GET/POST /v1/meetings`, `PATCH/DELETE /v1/meetings/{id}`  
**Speicher:** SQLite `{AIOS_MEMORY_ROOT}/state/meetings.db`

## Zweck

Zentrale manuelle Erfassung aller Meetings — Launchpad, Kollegen-Gespräche, Planung — **ohne Pflicht-Zuordnung** zu einem Projekt.

## Felder

| Feld | Pflicht | Hinweis |
|------|---------|---------|
| Titel | ja | |
| Datum/Uhrzeit | ja | ISO `held_at` |
| Teilnehmer | nein | Freitext; Google-Liste einfügen → E-Mail-Extraktion, optional Anreicherung (LinkedIn, Web), Upsert als `org:Person` im Graph |
| Kurzfassung | nein | |
| Projekte | nein | 0..n `eng:*` aus Brain + `active/*/README.md` |
| Tags | nein | z. B. `launchpad`, `kollegen`, `michael` |
| To-dos | nein | `{ text, done }` |
| **Anhänge** | nein | Dateien (PDF, Notizen, …) — max. 25 MB pro Datei |

## Anhänge

- Speicher: `{AIOS_MEMORY_ROOT}/state/meetings/attachments/{meeting_id}/`
- Metadaten: SQLite-Tabelle `meeting_attachments`
- API: `POST /v1/meetings/{id}/attachments` (multipart), Download/Delete per Attachment-ID
- Console: Datei-Upload im Meeting-Formular; bei neuem Meeting nach Speichern

## Teilnehmer aus Google-Kalender

1. Teilnehmerliste aus Google Kalender/Meet kopieren und ins Textfeld einfügen  
2. **Extrahieren & anreichern** — E-Mails parsen, bestehende Kontakte im Graph markieren, Firmenwebseite (Domain) und LinkedIn (DuckDuckGo-Suche) vorschlagen  
3. **Als Kontakte speichern** — `org:Person` + ggf. `org:Organization` im Knowledge Graph upserten; Meeting-Feld `participants` und `participant_refs` aktualisieren  

API: `POST /v1/meetings/participants/process`, `POST /v1/meetings/participants/commit`

## Filter

- Suche in Titel, Teilnehmer, Summary, Tags  
- **Ohne Projekt** — nur Meetings ohne `engagement_ids`  
- **Offene To-dos**

## Später

- Calendar-MCP → automatischer Import als `org:Meeting` (Graph)  
- Optional Sync kurierter Meetings aus Inbox → DP-Commit  
- Lagebild-Ask: „Was war im letzten Meeting?“ über federierte Suche
