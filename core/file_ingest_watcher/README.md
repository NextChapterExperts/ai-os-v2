# File-Ingest-Watcher

Übergangslösung, bis Fach-Agenten (Roadmap-Phase 4) Projektarbeit direkt
in AI-OS erledigen. Hintergrund & Entscheidung: [ADR 0002](../../docs/adr/0002-file-ingest-watcher-und-rolle-von-cursor.md).

Scannt periodisch `Projekte/active/**`, erkennt neue/geänderte/gelöschte
Dateien per SHA-256-Hash, extrahiert Text (Markdown/Code/PDF), chunked +
embedded lokal (`fastembed`) und schreibt in die Qdrant-Collection
`raw-files` — getrennt von der kuratierten Company-Brain-Collection
`content`.

## Betrieb

```bash
systemctl --user status aios-file-ingest-watcher.service
journalctl --user -u aios-file-ingest-watcher.service -f
```

## Manuell / einmalig laufen lassen

```bash
cd core/file_ingest_watcher
./run.sh --once
```

## Konfiguration (Env-Variablen, siehe `.service`-Datei)

| Variable | Default | Bedeutung |
|---|---|---|
| `WATCH_ROOTS` | `~/Projekte/active` | `:`-getrennte Liste zu scannender Wurzeln |
| `QDRANT_URL` | `http://127.0.0.1:6333` | Qdrant-Endpoint |
| `QDRANT_COLLECTION` | `raw-files` | Ziel-Collection |
| `EMBED_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | fastembed-Modell (mehrsprachig, 384-dim, lokal, CPU) |
| `SCAN_INTERVAL_SEC` | `300` | Wartezeit zwischen Scans |
| `STATE_DB` | `/opt/ai-os/ingest/file_watcher_state.db` | SQLite-Hash-Cache (Diff-Erkennung) |
| `MAX_FILE_SIZE_MB` | `25` | Dateien darüber werden übersprungen |
| `GIT_SNAPSHOT_ENABLED` | `true` | Auto-Commit im `Projekte`-Repo vor jedem Scan |
| `GIT_SNAPSHOT_REPO` | `~/Projekte` | Repo-Pfad für den Auto-Commit |

## Suche testen

```bash
cd core/file_ingest_watcher
.venv/bin/python search.py "meine suchanfrage" --limit 5
.venv/bin/python search.py "meine suchanfrage" --project active/waqam-doku
```

## Bekannte Grenzen (MVP)

- Nur Text/Code/Markdown/PDF — kein OCR, kein `.docx`/`.xlsx`/`.pptx`.
- `archive/` wird nicht gescannt (siehe ADR 0002).
- Ordner mit „archiv"/„backup" im Namen (case-insensitive Teilstring, z. B. `Archiv_Backups`, `_backup_20260627`) werden übersprungen, um Duplikate von Backup-Kopien in der Suche zu vermeiden.
- Kein Löschschutz: wird eine Datei gelöscht, verschwinden auch ihre
  Qdrant-Punkte beim nächsten Scan.
- Eigenes `.venv` (nicht das Root-`.venv`, das aktuell ohne `pip` gebaut ist).

## Erweitern

- Neue Textformate: `TEXT_EXTENSIONS` in `watcher.py` ergänzen.
- Office-Formate (`.docx`, `.pptx`): eigene Extraktion ergänzen (z. B. `python-docx`) oder auf `docling` umsteigen, sobald das im Stack ankommt.
- `archive/` mit aufnehmen: `WATCH_ROOTS` in der `.service`-Datei erweitern (Secrets in `archive/ai-os-v1` vorher prüfen/ausschließen).
