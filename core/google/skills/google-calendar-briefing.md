---
id: google-calendar-briefing
title: Kalender-Termine für Tages-Briefing laden
version: 1
created: 2026-08-03
tenant_id: nextchapter
produced_by: time-agent
success_rate: 0.0
use_count: 0
use_when:
  - daily-briefing Workflow: Termine heute
  - time-agent: org:Meeting aus Calendar-MCP
  - comms-manager: Teilnehmer aus Termin (`list_attendees`)
tags: [google, calendar, briefing, mcp]
---

## Ablauf

1. MCP: `calendar.get_today` → `{ date, summary, events[], status }`
2. Woche: `calendar.get_week` für 7-Tage-Übersicht
3. Teilnehmer: `calendar.list_attendees` mit `event_id` → comms-manager Input
4. Ohne OAuth: Gateway liefert Seed-Stub aus `calendar_stub.py` (status: stub)

## MCP-Tools

| Tool | Zweck |
|------|-------|
| `get_today` / `list_today` | Termine heute |
| `get_week` | Nächste 7 Tage |
| `get_event` | Vollständiges Event inkl. Beschreibung |
| `list_attendees` | Teilnehmer für Enrichment |

## Bekannte Fallstricke

- Zeitzone: `AI_OS_TIMEZONE` (Default `Europe/Berlin`) — nicht UTC für Anzeige
- Externer Sidecar (`mcp-calendar`) optional laut `config/mcp-servers.yaml` — nativer Adapter hat Vorrang
- `create_event` benötigt Schreib-Scope + `token_write.json` (noch nicht implementiert)

## Verbesserungen (Version 1)

- Port aus v1 `time-agent/scripts/tools/calendar_client.py`
