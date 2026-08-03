# MCP Gateway — native Google-Adapter

Allowlist + Handler für `mail`, `calendar`, `drive` (OAuth über `core/google/`).

```bash
./core/mcp_gateway/run.sh
# GET  http://localhost:8097/v1/servers
# POST http://localhost:8097/v1/call
```

Beispiel:

```bash
curl -s -X POST http://localhost:8097/v1/call \
  -H 'Content-Type: application/json' \
  -d '{"server": "calendar", "tool": "get_today", "arguments": {"dry_run": true}}'
```

Ohne `secrets/google/token.json` liefern mail/calendar Stub-Antworten; drive.poll_chats unterstützt Dry-Run.

Siehe `core/google/README.md` und `config/mcp-servers.yaml`.
