"""Postgres-Verbindung fuer den DP-Service (Knowledge Graph + Audit).

Bewusst NICHT von POSTGRES_HOST aus .env ableiten: der Wert ist docker-intern
("postgres-platform") und vom Host-Prozess (Orchestrator laeuft via systemd
direkt auf der VM) nicht aufloesbar. postgres-platform published seinen Port
zusaetzlich auf 127.0.0.1:5432 (deploy/infra.yml) - das nutzen wir hier,
analog zu core/orchestrator/handlers/unified_search.py fuer Qdrant.
"""

from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row

POSTGRES_URL = os.environ.get(
    "POSTGRES_URL_HOST",
    "postgresql://{user}:{password}@127.0.0.1:5432/{db}".format(
        user=os.environ.get("POSTGRES_USER", "aios"),
        password=os.environ.get("POSTGRES_PASSWORD", "changeme-aios-pg"),
        db=os.environ.get("POSTGRES_DB", "aios"),
    ),
)


def get_connection() -> psycopg.Connection:
    return psycopg.connect(POSTGRES_URL, row_factory=dict_row)
