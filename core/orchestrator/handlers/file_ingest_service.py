"""Universal File Ingest Service — PDF, Markdown, Text & Document Ingestion into AI-OS Memory.

Verarbeitet hochgeladene Dateien oder Ingest-Inbox Dateien:
1. Extrahiert Text & Frontmatter aus Markdown, Plaintext, PDF & Office-Dateien
2. Berechnet SHA256-Hash zur Deduplizierung
3. Speichert Kopie unter /opt/ai-os/ingest/inbox/documents/YYYY-MM-DD/
4. Schreibt FTS-Chunks in memory.db (SQLite `chunks` Tabelle)
5. Committet OrgKnowledgeAsset DataProduct in den Knowledge Graph (Postgres)
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.memory_gateway.sqlite_schema import ensure_schema
from core.orchestrator.dp_service import commit_dataproduct
from core.orchestrator.dataproducts import OrgKnowledgeAsset

MEMORY_DB = os.environ.get("AIOS_MEMORY_DB", "/opt/ai-os/memory/memory.db")
INBOX_ROOT = Path(os.environ.get("AIOS_INGEST_INBOX", "/opt/ai-os/ingest/inbox"))
DEFAULT_PROJECT = os.environ.get("AIOS_MEMORY_PROJECT", "home-peter-Projekte")


def _calculate_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def extract_text_from_file(filename: str, content: bytes) -> tuple[str, dict[str, Any]]:
    """Extrahiert Fließtext & Metadaten aus Datei-Content."""
    ext = Path(filename).suffix.lower()
    metadata: dict[str, Any] = {"filename": filename, "extension": ext, "size_bytes": len(content)}

    if ext in [".md", ".markdown", ".txt", ".csv", ".json", ".log"]:
        text = content.decode("utf-8", errors="replace")
        # Frontmatter Extraktion bei Markdown
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip().strip('"\'')
                text = parts[2].strip()
        return text, metadata

    elif ext == ".pdf":
        # Versuche PyPDF / pdfplumber falls verfügbar, sonst Plaintext-Fallback
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            pages_text = []
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt:
                    pages_text.append(f"--- Seite {idx + 1} ---\n{txt}")
            metadata["page_count"] = len(reader.pages)
            return "\n\n".join(pages_text), metadata
        except Exception:
            # Fallback falls PyPDF nicht installiert: rohe Strings filtern
            text = content.decode("ascii", errors="ignore")
            readable = re.sub(r"[^\w\s\.\,\:\;\-\_\/\(\)]+", " ", text)
            return readable[:20000], metadata

    else:
        # Fallback für sonstige Text-Formate
        return content.decode("utf-8", errors="replace")[:50000], metadata


def ingest_file_bytes(
    filename: str,
    content: bytes,
    *,
    tenant_id: str = "nextchapter",
    project_id: str | None = None,
    user_id: str = "default_user",
    published: bool = True,
) -> dict[str, Any]:
    """Ingestiert eine Datei aus Byte-Content atomar in Memory DB & Knowledge Graph."""
    file_hash = _calculate_sha256(content)
    text, meta = extract_text_from_file(filename, content)
    
    if not text.strip():
        raise ValueError(f"Datei {filename} enthält keinen extrahierbaren Text")

    pid = project_id or DEFAULT_PROJECT
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    inbox_dir = INBOX_ROOT / "documents" / day
    inbox_dir.mkdir(parents=True, exist_ok=True)
    
    safe_name = re.sub(r"[^\w\-\.]+", "_", filename)
    target_path = inbox_dir / f"{file_hash[:10]}_{safe_name}"
    target_path.write_bytes(content)

    # 1. In SQLite Memory DB FTS indezieren
    os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    cid = f"doc-{file_hash[:16]}"
    
    con = sqlite3.connect(MEMORY_DB)
    try:
        ensure_schema(con)
        con.execute(
            """
            INSERT INTO chunks (id, source, project_id, user_id, visibility, chat_id, role, title, body, source_path, created_at, ingested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              body=excluded.body, title=excluded.title, ingested_at=excluded.ingested_at
            """,
            (
                cid,
                "file_upload",
                pid,
                user_id,
                "team",
                f"file-{safe_name}",
                "document",
                filename[:80],
                text,
                str(target_path),
                now,
                now,
            ),
        )
        con.commit()
    finally:
        con.close()

    # 2. OrgKnowledgeAsset DataProduct erstellen und im KG committen
    dp = OrgKnowledgeAsset(
        tenant_id=tenant_id,
        produced_by="file-ingest-service",
        asset_id=f"asset-{file_hash[:12]}",
        title=filename,
        path=str(target_path.relative_to(INBOX_ROOT.parent) if target_path.is_relative_to(INBOX_ROOT.parent) else target_path),
        kind=meta.get("extension", ".txt").lstrip("."),
        published=published,
        canonical=True,
    )
    
    commit_res = commit_dataproduct(dp)

    return {
        "ok": True,
        "asset_id": dp.asset_id,
        "filename": filename,
        "hash": file_hash,
        "path": str(target_path),
        "chunk_id": cid,
        "text_length": len(text),
        "kg_commit": commit_res,
        "tenant_id": tenant_id,
    }
