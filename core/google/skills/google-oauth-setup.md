---
id: google-oauth-setup
title: Google OAuth für AI-OS V2 einrichten
version: 1
created: 2026-08-03
tenant_id: nextchapter
produced_by: platform
success_rate: 1.0
use_count: 0
use_when:
  - Erstmalige Google-Anbindung (Gmail, Kalender, Drive)
  - Token abgelaufen oder Scope-Fehler beim MCP-Call
tags: [google, oauth, setup, mcp]
---

## Ablauf

1. Google Cloud Console → APIs aktivieren: Gmail, Calendar, Drive, Sheets
2. OAuth-Client (Desktop) erstellen → JSON nach `secrets/google/credentials.json`
3. `python scripts/test_google_connection.py` — Browser-Login, Token in `secrets/google/token.json`
4. MCP-Gateway starten: `./core/mcp_gateway/run.sh`
5. Status prüfen: `POST /v1/call` mit `{ "server": "mail", "tool": "status" }`

## Bekannte Fallstricke

- **Scope-Fehler (v1-Bug behoben):** V2 prüft Scopes in `core/google/auth.py` vor jedem API-Call — nicht erst im Agenten
- Token ohne `drive`-Scope → `drive.poll_chats` schlägt fehl → Test-Skript erneut ausführen
- Container/VM: interaktiver Login nur auf Dev-VM; Token-Datei auf Ziel-VM kopieren (`secrets/google/`)

## Token-Varianten

| Datei | Wann |
|-------|------|
| `token.json` | Standard (read) |
| `token_gmail_modify.json` | Rechnungs-Pipeline, Label `R-Verarbeitet` |

## Verbesserungen (Version 1)

- v1: Scopes in `email-agent/google-tools` verstreut → v2: zentral `core/google/scopes.py`
