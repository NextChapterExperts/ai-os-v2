# Email-Agent (AIOS-PACK-EMAIL)

Fach-Agent für **Gmail-Rechnungen extrahieren** — ausschließlich MCP, Output als DataProducts.

**Release-Tag:** `roadmap/2026-08-03-p4-email-invoices`  
**Vollständige Spec:** [docs/21-EMAIL-AGENT-RECHNUNGEN.md](../../docs/21-EMAIL-AGENT-RECHNUNGEN.md)

## Console

- **Pfad:** `/agents` → Workflow **Gmail-Rechnungen extrahieren** (`email-invoices`)
- **Eingabe-DP (UI):** `InvoiceRunUserInput` (Modus, Archiv — keine technischen Felder)
- **Ausgabe-DP:** `InvoicePipelineReport`
- **Ressourcen:** `/api/agents/invoice-resources` (Sheet + Drive-Links)

## Intents (Orchestrator)

| Intent | Input-DP | Output-DP | Console |
|--------|----------|-----------|---------|
| `invoice_run` | `InvoiceRunRequest` | `InvoicePipelineReport` | ✅ Fachagent |
| `invoice_export` | `InvoiceExportRequest` | `InvoiceExport` | ⏳ nur Backend |

## MCP-Tools (mail-Server)

- `mail.status` — OAuth-Status
- `mail.preview_invoices` — Extract ohne Side-Effects
- `mail.run_invoices` — volle Pipeline (Gmail → Sheet → Drive → Label)
- `mail.export_steuer` — Steuer-PDF-Export (Backend)

## Konfiguration

`config/invoice.yaml` oder `customers/{tenant}/config/invoice.yaml`

## OAuth

`secrets/google/credentials.json`, `token.json` (+ `token_gmail_modify.json` für Label `R-Verarbeitet`)

Verbindungstest: `python scripts/test_google_connection.py`

## Wartung (kein Agent)

```bash
export PYTHONPATH=$PWD GOOGLE_TOOLS_SECRETS=$PWD/secrets/google
.venv/bin/python scripts/backfill-invoice-sheet-from-drive.py --dry-run
```

## Tests

```bash
python -m pytest tests/test_email_agent.py tests/test_google_invoices_regression.py \
  tests/test_invoice_parse.py tests/test_invoice_backfill.py \
  tests/test_platform_gate.py -k "gate_6 or gate_7 or gate_8 or gate_9 or gate_10 or gate_11 or gate_12" -q
```
