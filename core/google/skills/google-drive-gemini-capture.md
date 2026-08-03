---
id: google-drive-gemini-capture
title: Gemini-Chats aus Google Drive ins Gedächtnis importieren
version: 1
created: 2026-08-03
tenant_id: nextchapter
produced_by: chat-capture
success_rate: 0.0
use_count: 0
use_when:
  - Gemini „In Drive speichern" → L1/L2 über chat-import
  - Phase 1b Drive-Poller (Roadmap ⏳ → ✅ V2)
  - Console /platform/capture Status + manueller Poll
tags: [google, drive, gemini, capture, chat-import]
---

## Ablauf

1. Quelle in `config/chat-sources.yaml` (`mode: drive_poll`, `drive_folder_id`)
2. Dry-Run: `python core/capture/gemini-drive-poller.py --dry-run --json-lines`
3. Live: Poller ruft `core.orchestrator.chat_import.import_transcript` auf
4. MCP-Alternative: `drive.poll_chats` mit `{ "source_id": "gemini-workspace", "live": true }`
5. Ergebnis: Chunks in SQLite FTS + optional Letta L2 — **kein** org:Claim (Roadmap 1b.6)

## Export-Formate

| MIME | Behandlung |
|------|------------|
| Google Doc | `export` → text/plain |
| `vnd.google-gemini.conversation` | Protobuf → lesbare UTF-8-Läufe extrahieren |
| Sheets/Slides | übersprungen |

## State

- Incremental: `AIOS_GEMINI_DRIVE_STATE` speichert `file_id → modifiedTime`
- `--force` ignoriert State (Re-Import)

## Bekannte Fallstricke

- Ordner-ID robuster als Name — in chat-sources.yaml pflegen
- v1 nutzte `email-agent/google-tools/secrets` — v2: `secrets/google/`
- Browser-Backfill (`gemini-privat`) läuft lokal, nicht im Container

## Verbesserungen (Version 1)

- Port aus v1 `chat-agent/google-tools/scripts/chat_drive_poller.py`
