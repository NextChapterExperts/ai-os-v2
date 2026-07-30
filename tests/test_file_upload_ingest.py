"""Pytest Suite — Universal File Ingest Service & Upload API Tests."""

import os
import sys
import pytest
from fastapi.testclient import TestClient

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from core.orchestrator.handlers.file_ingest_service import extract_text_from_file, ingest_file_bytes
from core.orchestrator.server import app

client = TestClient(app)


def test_extract_text_markdown():
    """Prüft die Extraktion von Text und Frontmatter aus Markdown-Dateien."""
    content = b"---\ntitle: \"Test Doku\"\nauthor: \"AI-OS\"\n---\n\n# Ueberschrift\nDas ist ein Test-Text."
    text, meta = extract_text_from_file("doku.md", content)
    
    assert "Ueberschrift" in text
    assert meta["title"] == "Test Doku"
    assert meta["author"] == "AI-OS"
    assert meta["extension"] == ".md"


def test_ingest_file_bytes_direct():
    """Prüft die direkte Ingestion von Byte-Content mit Memory-DB & DataProduct Commit."""
    content = b"Beispielhafter Vertragsentwurf fuer Malerarbeiten.\nKosten: 5000 EUR."
    res = ingest_file_bytes("vertrag.txt", content, tenant_id="nextchapter")

    assert res["ok"] is True
    assert res["filename"] == "vertrag.txt"
    assert res["text_length"] > 0
    assert "asset_id" in res
    assert "kg_commit" in res
    assert res["kg_commit"]["node_type"] == "org:KnowledgeAsset"


def test_upload_file_ingest_rest_endpoint():
    """Prüft den REST-Endpoint POST /v1/ingest/upload via FastAPI TestClient."""
    file_payload = ("anweisung.md", b"# Sicherheitspolicy\nAlle Daten muessen verschluesselt werden.")
    
    response = client.post(
        "/v1/ingest/upload",
        files={"file": file_payload},
        data={"tenant_id": "nextchapter"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["filename"] == "anweisung.md"
    assert "asset_id" in data
