"""Tests for Multi-User Layer and 3-Tier Visibility Architecture (user_id + visibility)."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import pytest

from core.memory_gateway.sqlite_schema import ensure_schema
from core.memory_gateway.persist import persist_chat_turn
from core.orchestrator.chat_import import import_transcript
from core.orchestrator.context_resolution import resolve_context_async
from core.orchestrator.memory_store import (
    chunks_in_window,
    search_chunks,
    search_chunks_fts,
)


@pytest.fixture
def temp_memory_db(monkeypatch):
    """Temporary memory.db for test isolation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_memory.db")
        monkeypatch.setenv("AIOS_MEMORY_DB", db_path)
        import core.memory_gateway.sqlite_schema as schema_mod
        import core.memory_gateway.persist as persist_mod
        import core.orchestrator.chat_import as import_mod
        import core.orchestrator.memory_store as store_mod

        monkeypatch.setattr(schema_mod, "MEMORY_DB", db_path)
        monkeypatch.setattr(persist_mod, "MEMORY_DB", db_path)
        monkeypatch.setattr(import_mod, "MEMORY_DB", db_path)
        monkeypatch.setattr(store_mod, "MEMORY_DB", db_path)

        con = sqlite3.connect(db_path)
        ensure_schema(con)
        con.close()

        yield db_path


def test_schema_has_user_columns(temp_memory_db):
    con = sqlite3.connect(temp_memory_db)
    cols = {r[1] for r in con.execute("PRAGMA table_info(chunks)").fetchall()}
    con.close()
    assert "user_id" in cols
    assert "visibility" in cols


def test_persist_chat_turn_visibility(temp_memory_db):
    res_a = persist_chat_turn(
        tenant_id="nextchapter",
        messages=[{"role": "user", "content": "Geheimes Gehaltsgespräch mit HR"}],
        assistant_content="Vertrauliche Notiz gespeichert.",
        session_id="hr-session-1",
        produced_by="test",
        model="sovereign",
        user_id="user_alice",
        visibility="private",
    )
    assert res_a["persisted"] == 2

    res_b = persist_chat_turn(
        tenant_id="nextchapter",
        messages=[{"role": "user", "content": "Offizielle Firmen-Policy für Urlaub"}],
        assistant_content="Hier ist die Urlaubs-Policy.",
        session_id="company-session-1",
        produced_by="test",
        model="sovereign",
        user_id="user_bob",
        visibility="company",
    )
    assert res_b["persisted"] == 2

    # Alice searches for HR secret -> MUST find it
    alice_hits = search_chunks_fts("Gehaltsgespräch", user_id="user_alice")
    assert len(alice_hits) > 0

    # Bob searches for HR secret -> MUST NOT find it (it is private to Alice)
    bob_hits = search_chunks_fts("Gehaltsgespräch", user_id="user_bob")
    assert len(bob_hits) == 0

    # Both Alice and Bob search for official company policy -> Both MUST find it
    alice_policy = search_chunks_fts("Urlaubs-Policy", user_id="user_alice")
    bob_policy = search_chunks_fts("Urlaubs-Policy", user_id="user_bob")
    assert len(alice_policy) > 0
    assert len(bob_policy) > 0


def test_chat_import_with_user(temp_memory_db):
    transcript = {
        "source": "antigravity",
        "external_id": "conv-12345",
        "messages": [
            {"role": "user", "text": "Mein privater Entwurf für das Projekt Alpha"},
            {"role": "assistant", "text": "Entwurf wurde erstellt."},
        ],
    }
    res = import_transcript(
        transcript,
        tenant_id="nextchapter",
        project_id="home-peter-Projekte",
        user_id="user_charlie",
        visibility="private",
    )
    assert res["ok"] is True
    assert res["chunk_count"] == 2

    charlie_hits = search_chunks("Projekt Alpha", user_id="user_charlie")
    assert len(charlie_hits) > 0

    dave_hits = search_chunks("Projekt Alpha", user_id="user_dave")
    assert len(dave_hits) == 0


@pytest.mark.asyncio
async def test_context_resolution_user_slice():
    bundle = await resolve_context_async(
        intent="ping",
        tenant_id="nextchapter",
        params={"user_id": "user_eve"},
    )
    assert bundle["system"]["user_id"] == "user_eve"
    assert bundle["system"]["tenant"] == "nextchapter"
