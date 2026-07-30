# 15-FILE-INGESTION.md — Universal File Ingestion & DataProduct Extraction

> **Zweck:** Technische Dokumentation für die automatische Ingestion von Dateien (PDF, Markdown, Text, CSV, DOCX), FTS-Indizierung und DataProduct Knowledge Asset Konvertierung in AI-OS v2.

---

## 1. Überblick & Datenfluss

Die File Ingestion Pipeline ermöglicht es Nutzern und externen Quellen, Dokumente in das AI-OS Gedächtnis zu laden:

```
[ Drag & Drop UI / REST API / Inbox Watcher ]
                     │
                     ▼
       POST /v1/ingest/upload (Orchestrator)
                     │
                     ├─► 1. Text & Frontmatter Extraktion (Markdown, PDF, TXT)
                     ├─► 2. SHA256 Hash-Generierung (Deduplizierung)
                     ├─► 3. Archivierung unter /opt/ai-os/ingest/inbox/documents/YYYY-MM-DD/
                     ├─► 4. SQLite FTS Indizierung (Tabelle `chunks` in memory.db)
                     └─► 5. OrgKnowledgeAsset DataProduct Commit (Knowledge Graph Postgres)
```

---

## 2. API Spezifikation

### `POST /v1/ingest/upload`

Exportierter Endpoint des Core Orchestrators (`:8091`).

* **Content-Type:** `multipart/form-data`
* **Form Parameter:**
  * `file`: Datei (PDF, MD, TXT, CSV, JSON)
  * `tenant_id`: Mandant (Default: `nextchapter`)
  * `project_id`: Optionale Projekt-Zuordnung
  * `user_id`: Benutzer-ID (Default: `default_user`)

* **Beispiel-Response:**
```json
{
  "ok": true,
  "asset_id": "asset-7f8a9b0c1d2e",
  "filename": "Baustellen_Aufmass.pdf",
  "hash": "7f8a9b0c1d2e3f4a...",
  "path": "/opt/ai-os/ingest/inbox/documents/2026-07-30/7f8a9b0c1d_Baustellen_Aufmass.pdf",
  "chunk_id": "doc-7f8a9b0c1d2e3f4a",
  "text_length": 4520,
  "kg_commit": {
    "node_id": "104",
    "node_type": "org:KnowledgeAsset",
    "external_id": "asset-7f8a9b0c1d2e",
    "ingest_queued": true
  },
  "tenant_id": "nextchapter"
}
```

---

## 3. UI-Integration

Die Console Web UI (`:8092`) stellt unter `/workflows` ein interaktives **Drag-and-Drop Formular** (`FileUploadDropzone.tsx`) bereit:

* **Next.js Proxy API:** `/api/ingest/upload`
* **Rückmeldung:** Sofortige Anzeige von Verarbeitungsstatus, Textlänge und generierter Asset-ID.

---

## 4. Speicherorte & Retention

| Typ | Speicherort | Zweck |
|-----|-------------|-------|
| Rohdatei | `/opt/ai-os/ingest/inbox/documents/YYYY-MM-DD/` | Originalarchiv |
| FTS Chunks | `/opt/ai-os/memory/memory.db` (`chunks`) | Schnelle Volltextsuche & Lagebild |
| Graph Node | Postgres `kg_nodes` (`node_type='org:KnowledgeAsset'`) | Beziehungs- & Wissensnetzwerk |

---

*Dieses Dokument gehört zur offiziellen AI-OS v2 Dokumentationsserie.*
