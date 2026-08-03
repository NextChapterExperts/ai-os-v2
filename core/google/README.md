# Google OAuth & API — AI-OS V2 Plattform-Kern

Zentraler Google-Zugriff für MCP-Adapter (`mail`, `calendar`, `drive`) und Capture-Jobs.

Portiert aus v1 `packages/email-agent/google-tools` und `packages/chat-agent/google-tools`.

## Struktur

```
core/google/
├── auth.py              # OAuth (Scope-Validierung vor jedem Call — v2-Fix ce07801)
├── scopes.py            # MCP-Tool → OAuth-Scope-Mapping
├── gmail_client.py      # Gmail lesen, Labels (modify-Token)
├── calendar_client.py   # Termine, Teilnehmer
├── drive_client.py      # Ordner, Text-Export (Gemini-Chats)
├── skills/              # V2 Skill-Dokumente (Skill-Loop §14)
└── requirements.txt

secrets/google/          # credentials.json + token*.json — NICHT committen
config/chat-sources.yaml # Drive-Poll-Quellen (Phase 1b)
config/mcp-servers.yaml  # Allowlist + Caps
```

## Einrichtung

```bash
# 1. OAuth-Client-JSON aus Google Cloud Console
mkdir -p secrets/google
cp ~/Downloads/client_secret_*.json secrets/google/credentials.json

# 2. Dependencies
pip install -r core/google/requirements.txt

# 3. Interaktive Autorisierung (Browser)
python scripts/test_google_connection.py
```

## MCP-Tools (über Gateway :8097)

| Server | Tool | Scope |
|--------|------|-------|
| `mail` | `get_recent`, `get_by_id`, `parse_headers`, `status` | gmail.readonly |
| `calendar` | `get_today`, `get_week`, `list_attendees`, `get_event` | calendar.readonly |
| `drive` | `list_sources`, `poll_chats`, `list_folder` | drive |

Agenten rufen **nur** über `sdk.MCPAdapter` auf — nie direkt `googleapiclient`.

## Gemini Drive Capture

```bash
# Dry-Run
python core/capture/gemini-drive-poller.py --dry-run --json-lines

# Live-Import → chat-import → L1/L2
python core/capture/gemini-drive-poller.py --source-id gemini-workspace

# systemd (VM)
systemctl --user enable core/capture/aios-gemini-drive.service
```

## Umgebungsvariablen

| Variable | Default |
|----------|---------|
| `GOOGLE_TOOLS_SECRETS` | `{REPO}/secrets/google` |
| `AIOS_CHAT_SOURCES` | `config/chat-sources.yaml` |
| `AIOS_GEMINI_DRIVE_STATE` | `{AIOS_MEMORY_ROOT}/state/gemini-drive-state.json` |
| `GOOGLE_CREDENTIALS_JSON` | Sidecar-Calendar (M2, optional) |

## Token-Dateien

| Datei | Verwendung |
|-------|------------|
| `token.json` | Lesen: Gmail, Kalender, Drive, Sheets |
| `token_gmail_modify.json` | Gmail-Labels (Rechnungen) |
| `token_write.json` | Kalender/Tasks schreiben (optional) |

## Skills

Operative Anleitungen liegen unter `core/google/skills/` im V2 Skill-Loop-Format (Roadmap §14).
