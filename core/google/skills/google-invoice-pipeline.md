---
id: google-invoice-pipeline
title: Gmail-Rechnungen extrahieren, archivieren und ins Sheet schreiben
version: 1
created: 2026-08-03
tenant_id: nextchapter
produced_by: email-agent
success_rate: 0.0
use_count: 0
use_when:
  - Rechnungs-Mails aus Gmail ins Business-Sheet übernehmen
  - PDF-Anhänge nach Google Drive archivieren
  - Intent invoice_run oder Dispatch an email-agent
tags: [google, gmail, invoice, email-agent, mcp]
---

## Ablauf (V2 — nur MCP)

1. Konfiguration: `config/invoice.yaml` (Sheet-ID, Gmail-Queries, Drive-Ordner)
2. OAuth: `secrets/google/token.json` + `token_gmail_modify.json` für Label `R-Verarbeitet`
3. Dispatch: `POST /v1/dispatch` Intent `invoice_run` mit `{ "dry_run": true }` zum Testen
4. Agent ruft `mail.run_invoices` über MCP-Gateway auf — **kein** direkter googleapiclient im Agent
5. Output-DP: `InvoicePipelineReport` → Commit nach `G` (email:Invoice-Knoten)

## MCP-Tools

| Tool | Phase |
|------|-------|
| `mail.preview_invoices` | Extract only |
| `mail.run_invoices` | Extract → Drive → Sheet → Label |
| `mail.export_steuer` | Steuer-PDF-Export lokal |

## Pipeline-Phasen (deterministisch)

1. **Extract** — Gmail-Scan, Felder parsen (kein LLM)
2. **Archive** — PDF → Drive (`Rechnungen/{year}/{month}`)
3. **Sheet** — Spalten A–L, Dedup über Spalte J
4. **Label** — Gmail `R-Verarbeitet`

## Bekannte Fallstricke

- Scope-Fehler: `run_invoices` braucht gmail + drive + spreadsheets
- PII in Summary wird vor Speicherung redigiert (`pii_cleared` im DP)
- v1 `invoice_pipeline.py` → v2 `core/google/invoice/pipeline.py` + MCP

## Verbesserungen (Version 1)

- Architektur: Agent → MCP → core/google/invoice (P5 konform)
