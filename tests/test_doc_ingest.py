"""Unit tests for Project Docs Ingester (doc_ingest.py)."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import pytest

from core.ingest_agent.doc_ingest import ingest_project_docs, parse_markdown_sections
from core.memory_gateway.sqlite_schema import ensure_schema
from core.orchestrator.memory_store import search_chunks_fts


def test_parse_markdown_sections(tmp_path):
    doc = tmp_path / "test_doc.md"
    doc.write_text(
        "# Header 1\n\nBody text for section 1.\n\n## Subheader A\n\nDetailed content for subheader A.\n",
        encoding="utf-8",
    )
    sections = parse_markdown_sections(doc)
    assert len(sections) >= 1
    titles = [s["title"] for s in sections]
    assert any("Header 1" in t for t in titles)


def test_ingest_project_docs(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_doc_memory.db")
        monkeypatch.setenv("AIOS_MEMORY_DB", db_path)
        import core.orchestrator.memory_store as store_mod
        monkeypatch.setattr(store_mod, "MEMORY_DB", db_path)

        res = ingest_project_docs(db_path=db_path, project_id="1100-AI-OS-V2", user_id="person:peter-alexander")
        assert res["files"] > 0
        assert res["chunks"] > 0

        con = sqlite3.connect(db_path)
        ensure_schema(con)
        count = con.execute("SELECT COUNT(*) FROM chunks WHERE source = 'docs'").fetchone()[0]
        con.close()
        assert count > 0

        # Search for known doc terms
        hits = search_chunks_fts("Leitprinzipien", user_id="person:peter-alexander")
        assert len(hits) > 0
