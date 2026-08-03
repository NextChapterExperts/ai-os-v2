---
id: google-gmail-access
title: Gmail über MCP mail-Adapter lesen
version: 1
created: 2026-08-03
tenant_id: nextchapter
produced_by: email-agent
success_rate: 0.0
use_count: 0
use_when:
  - Postfach abfragen, ungelesene Mails listen
  - Mail-Header für comms-manager-agent parsen
  - Tages-Briefing: offene Mail-Aktionen
tags: [google, gmail, mail, mcp]
---

## Ablauf

1. Scope prüfen: `gmail.readonly` in `token.json` (siehe Skill `google-oauth-setup`)
2. MCP-Call über Agent: `await self.mcp.call("mail", "get_recent", {"max": 20, "only_unseen": true})`
3. Einzelne Mail: `mail.get_by_id` mit `id` aus Thread-Liste
4. Teilnehmer-Enrichment: `mail.parse_headers` → E-Mail + Betreff an comms-manager

## MCP-Tools

| Tool | Argumente | Output |
|------|-----------|--------|
| `status` | — | Google konfiguriert ja/nein |
| `get_recent` | `max`, `only_unseen`, `q` | `threads[]` |
| `get_by_id` | `id` | `message` mit Body |
| `parse_headers` | `id` | `from`, `to`, `cc`, `subject` |
| `list_open_actions` | `tenant_id` | Briefing-kompatible `actions[]` |

## Bekannte Fallstricke

- Kein direkter `googleapiclient`-Import in Agenten — nur MCP (P5)
- Modify-Scope (`token_gmail_modify.json`) nur für Label-Operationen, nicht für Lesen
- v1 Rechnungs-Pipeline portiert → `core/google/invoice/` + MCP `mail.run_invoices` + `agents/email/`

## Verbesserungen (Version 1)

- Port aus v1 `mcp_adapters.py` mail.* + `gmail_client.py`
