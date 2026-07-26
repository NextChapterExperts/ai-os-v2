"""Doc-Ingester — Indiziert Projektdokumente (docs/*.md, ROADMAP.md, AGENTS.md) in memory.db & Qdrant."""

from __future__ import annotations

import hashlib
import logging
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.memory_gateway.sqlite_schema import ensure_schema, rebuild_fts

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("doc-ingest")

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DB = os.environ.get("AIOS_MEMORY_DB", "/opt/ai-os/memory/memory.db")
DEFAULT_PROJECT = "1100-AI-OS-V2"
DEFAULT_USER = "person:peter-alexander"
DEFAULT_VISIBILITY = "company"


def _chunk_id(rel_path: str, title: str, body: str, index: int) -> str:
    raw = f"{rel_path}:{index}:{title}:{body[:100]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def parse_markdown_sections(filepath: Path) -> list[dict[str, Any]]:
    """Zerlegt ein Markdown-Dokument nach Überschriften in logische Abschnitte."""
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    sections: list[dict[str, Any]] = []
    current_title = filepath.name
    current_lines: list[str] = []

    for line in lines:
        match = re.match(r"^(#{1,4})\s+(.+)", line)
        if match:
            if current_lines:
                body = "\n".join(current_lines).strip()
                if len(body) >= 20:
                    sections.append({"title": current_title, "body": body})
                current_lines = []
            current_title = f"{filepath.name} — {match.group(2).strip()}"
        else:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if len(body) >= 20:
            sections.append({"title": current_title, "body": body})

    return sections


def collect_doc_files() -> list[Path]:
    """Sammelt alle zu indizierenden Projektdokumente."""
    docs: list[Path] = []
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        for p in sorted(docs_dir.rglob("*.md")):
            docs.append(p)

    for root_doc in ["ROADMAP.md", "AGENTS.md", "README.md"]:
        p = REPO_ROOT / root_doc
        if p.exists():
            docs.append(p)

    return docs


def ingest_project_docs(
    *,
    db_path: str = MEMORY_DB,
    project_id: str = DEFAULT_PROJECT,
    user_id: str = DEFAULT_USER,
    visibility: str = DEFAULT_VISIBILITY,
) -> dict[str, Any]:
    """Liest alle Projektdokumente und schreibt Chunks in memory.db."""
    doc_files = collect_doc_files()
    if not doc_files:
        log.warning("Keine Dokudateien gefunden in %s", REPO_ROOT)
        return {"files": 0, "chunks": 0}

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    ensure_schema(con)

    now = datetime.now(timezone.utc).isoformat()
    total_chunks = 0
    written_ids: list[str] = []

    upsert = """
        INSERT INTO chunks (id, source, project_id, user_id, visibility, chat_id, role, title, body, source_path, created_at, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          body=excluded.body, title=excluded.title, user_id=excluded.user_id, visibility=excluded.visibility, ingested_at=excluded.ingested_at
    """

    try:
        for doc_path in doc_files:
            rel_path = str(doc_path.relative_to(REPO_ROOT))
            mtime = datetime.fromtimestamp(doc_path.stat().st_mtime, timezone.utc).isoformat()
            sections = parse_markdown_sections(doc_path)

            for idx, sec in enumerate(sections):
                cid = _chunk_id(rel_path, sec["title"], sec["body"], idx)
                con.execute(
                    upsert,
                    (
                        cid,
                        "docs",
                        project_id,
                        user_id,
                        visibility,
                        doc_path.name,
                        "document",
                        sec["title"][:120],
                        sec["body"][:15000],
                        rel_path,
                        mtime,
                        now,
                    ),
                )
                written_ids.append(cid)
                total_chunks += 1

        con.commit()
        rebuild_fts(con)
    finally:
        con.close()

    log.info("Doc-Ingest abgeschlossen: %d Dateien → %d Chunks in memory.db", len(doc_files), total_chunks)
    return {
        "files": len(doc_files),
        "chunks": total_chunks,
        "chunk_ids": written_ids,
    }


if __name__ == "__main__":
    res = ingest_project_docs()
    print(f"Doc-Ingest Ergebnis: {res['files']} Dateien, {res['chunks']} Chunks indiziert.")
