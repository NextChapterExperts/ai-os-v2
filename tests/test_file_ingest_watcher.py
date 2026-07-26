"""File Ingest Watcher Tests (Text Extraction, Word Chunking, Hashing)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.file_ingest_watcher import watcher


def test_is_ignored_dir():
    assert watcher._is_ignored_dir(".git") is True
    assert watcher._is_ignored_dir("node_modules") is True
    assert watcher._is_ignored_dir(".venv") is True
    assert watcher._is_ignored_dir("Archiv_2026") is True
    assert watcher._is_ignored_dir("my_backup_folder") is True
    assert watcher._is_ignored_dir("src") is False
    assert watcher._is_ignored_dir("active") is False


def test_sha256_of_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello AI-OS Watcher", encoding="utf-8")
    h1 = watcher.sha256_of(f)
    h2 = watcher.sha256_of(f)
    assert h1 == h2
    assert len(h1) == 64


def test_point_id_for_stable():
    p1 = watcher.point_id_for("/home/peter/test.md", 0)
    p2 = watcher.point_id_for("/home/peter/test.md", 0)
    p3 = watcher.point_id_for("/home/peter/test.md", 1)
    assert p1 == p2
    assert p1 != p3


def test_chunk_text_word_aware():
    sample_text = (
        "The AI-OS Company Brain architecture uses a multi-layered storage system. "
        "Layer 1 contains curated Knowledge Assets, Layer 2 aggregates daily digests, "
        "and Layer 3 extracts verified claims into the Knowledge Graph."
    )
    chunks = watcher.chunk_text(sample_text, size=80, overlap=10)
    assert len(chunks) >= 2
    # Ensure chunks do not cut words abruptly if spaces exist
    for c in chunks:
        assert len(c) <= 90
        assert not c.startswith(" ")
        assert not c.endswith(" ")


def test_extract_text_markdown_with_frontmatter(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text(
        "---\ntitle: 'Test Document'\nauthor: 'Peter'\n---\n\n# Header\n\nContent body here.",
        encoding="utf-8",
    )
    content, meta = watcher.extract_text(f)
    assert "Content body here." in content
    assert meta.get("title") == "Test Document"
    assert meta.get("author") == "Peter"
