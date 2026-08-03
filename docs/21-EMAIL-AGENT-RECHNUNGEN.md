# Fachagent: Gmail-Rechnungen extrahieren (`email-agent`)

**Roadmap:** [ROADMAP.md §9.3](../ROADMAP.md#93-email-agent)  
**Release-Tag:** `roadmap/2026-08-03-p4-email-invoices` (siehe [22-RELEASE-TAGS.md](22-RELEASE-TAGS.md))  
**SKU-Pfad:** `agents/email/` · **Workflow-ID (Console):** `email-invoices`

---

## Zweck

Der Email-Fachagent automatisiert die **Rechnungs-Pipeline** für den Mandanten `nextchapter`:

1. Gmail nach Rechnungs-Kandidaten durchsuchen  
2. PDF-Anhänge per **pypdf + optional OCR (Tesseract)** auslesen  
3. Felder deterministisch extrahieren (Regex — kein LLM im Kernpfad)  
4. PDFs in Google Drive archivieren (`Rechnungen/{Jahr}/{Monat}/`)  
5. Neue Zeilen ins Google Sheet schreiben (Spalten A–L)  
6. Verarbeitete Mails mit Gmail-Label `R-Verarbeitet` markieren  

**Architekturregel (P5/P8):** Der Agent ruft **ausschließlich MCP** auf (`mail.run_invoices`). Kein direkter Google-Client im Agent-Code.

---

## Console-UI (Fachagenten-Cockpit)

| Element | Pfad / Verhalten |
|---------|------------------|
| Navigation | **Agenten** → `/agents` |
| Fachagent | **Gmail-Rechnungen extrahieren** (`workflow_id: email-invoices`) |
| Eingabe | Generisches Formular aus `InvoiceRunUserInput` (JSON Schema) |
| Ausgabe | `DataProductViewer` → `InvoicePipelineReport` |
| Sheet/Drive-Links | `/api/agents/invoice-resources` → Google Sheet + Drive-Ordner |

### Nutzer-Eingabe (nur verständliche Felder)

| Feld | Optionen |
|------|----------|
| **Ausführungsmodus** | Nur Vorschau (Dry-Run) · Live — Sheet & Drive aktualisieren |
| **PDF-Archiv in Drive** | PDFs archivieren · Archivierung überspringen |

Interne DataProduct-Felder (`workflow_run_id`, `tenant_id`, …) werden **nicht** in der UI angezeigt.

---

## DataProducts

| Richtung | Typ | Beschreibung |
|----------|-----|--------------|
| Input (UI) | `InvoiceRunUserInput` | Console-Formular |
| Input (Agent) | `InvoiceRunRequest` | Intern nach Mapping |
| Output | `InvoicePipelineReport` | Kandidaten, geschriebene Zeilen, Sheet-URL, `invoices[]` |
| Zeile | `InvoiceRecord` | Einzelne Rechnung (Sheet-Zeile + Metadaten) |

Steuer-Export (`InvoiceExport`) bleibt als **Dispatch-Intent** `invoice_export` im Backend — **kein** separater Console-Fachagent.

---

## MCP-Tools (`mail`-Server)

| Tool | Scope | Funktion |
|------|-------|----------|
| `mail.status` | gmail.readonly | OAuth-Status |
| `mail.preview_invoices` | gmail.readonly | Gmail-Scan ohne Schreiben |
| `mail.run_invoices` | gmail.readonly, spreadsheets, drive | Volle Pipeline |
| `mail.export_steuer` | gmail.readonly, drive | Steuer-Export (Backend) |

Allowlist: `config/mcp-servers.yaml`

---

## Plattform-Kern (kein Agent-Code)

```
core/google/
├── auth.py              OAuth (Scope-Fix: volle Token-Scopes beim Refresh)
├── gmail_client.py      Gmail lesen, Labels
├── drive_client.py      Ordner-Auflösung
├── invoice/
│   ├── extract.py       Regex-Parser, Gmail-Fetch, Sheet I/O
│   ├── mime.py          PDF/.eml verschachtelt
│   ├── archive.py       PDF → Drive
│   ├── pipeline.py      Orchestrierung
│   ├── pdf_text.py      pypdf + OCR-Fallback
│   ├── enrich.py        Body + PDF-Text kombinieren
│   └── backfill.py      Sheet-Nachpflege aus Drive-PDFs

core/mcp_gateway/adapters/mail.py   MCP-Handler
core/workflow_engine/email_workflows.py   Registry `email-invoices`
agents/email/agent.py               EmailAgent (MCP-only)
```

---

## Google Sheet (Spalten A–L)

Konfiguration: `config/invoice.yaml`

| Spalte | Feld | Quelle |
|--------|------|--------|
| A | Lieferant | `infer_vendor()` |
| B | Zweck | `extract_purpose()` |
| C | Betrag | `extract_amount()` (+ PDF-Text) |
| D | Intervall | `infer_interval()` |
| E | Vertragsbeginn | Mail-Datum / PDF |
| F | Nächste Verlängerung | `extract_next_renewal()` |
| G | Kündigungsfrist | `extract_cancellation_days()` |
| H | Letzter Kündigungstag | Formel im Sheet |
| I | Zahlungsmethode | `extract_payment_method()` |
| J | Rechnungs-Nr. | Dedup-Key |
| K | Status | Default „Prüfen“ |
| L | Drive-Link | Nach Archivierung |

---

## Backfill (Wartung, kein Agent)

Einmaliges Nachpflegen historischer Sheet-Zeilen aus bereits archivierten Drive-PDFs:

```bash
export PYTHONPATH=$PWD GOOGLE_TOOLS_SECRETS=$PWD/secrets/google

# Dry-Run
.venv/bin/python scripts/backfill-invoice-sheet-from-drive.py --dry-run

# Live (leere Felder füllen)
.venv/bin/python scripts/backfill-invoice-sheet-from-drive.py

# Bestehende Werte überschreiben
.venv/bin/python scripts/backfill-invoice-sheet-from-drive.py --force
```

Gleiche Extraktions-Pipeline wie der Agent (`pdf_text.py` + `extract.py`).

---

## OAuth & Secrets

| Datei | Zweck |
|-------|--------|
| `secrets/google/credentials.json` | OAuth-Client |
| `secrets/google/token.json` | Haupt-Token (Gmail, Drive, Sheets) |
| `secrets/google/token_gmail_modify.json` | Label `R-Verarbeitet` |

Verbindungstest: `python scripts/test_google_connection.py`

---

## Dispatch-Intents

| Intent | Handler |
|--------|---------|
| `invoice_run` | `core/orchestrator/handlers/invoice_pipeline.py` |
| `invoice_export` | Steuer-Export (Backend) |

Orchestrator-API: `GET/POST /v1/email/invoices/*` (Status, Preview, Run)

---

## Tests

| Datei | Inhalt |
|-------|--------|
| `tests/test_platform_gate.py` | Gate 6–12 (Invoice-Stack) |
| `tests/test_google_invoices_regression.py` | MCP, Agent, Parser |
| `tests/test_invoice_parse.py` | Regex-Parser |
| `tests/test_invoice_backfill.py` | Backfill-Matching |
| `tests/test_email_agent.py` | MCP-only Contract |

```bash
python -m pytest tests/test_platform_gate.py tests/test_google_invoices_regression.py \
  tests/test_invoice_parse.py tests/test_invoice_backfill.py tests/test_email_agent.py -q
```

---

## Bekannte Grenzen & nächste Schritte

| Thema | Status |
|-------|--------|
| PDF-Text-Extraktion (pypdf) | ✅ |
| OCR für Scans (Tesseract) | ✅ optional (`pipeline.pdf_ocr_fallback`) |
| LLM-Fallback für unleserliche PDFs | ⏳ Roadmap Phase 4+ |
| Re-Extract ohne `--force` nur leere Felder | ✅ Backfill |
| Console: kein eigener Plattform-Tab | ✅ nur `/agents` |
