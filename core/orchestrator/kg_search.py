"""Graph-Suche — macht den Knowledge Graph (G) tatsaechlich durchsuchbar.

Bisher gab es nur `resolve_node_by_id` (exakte ID) und `kg_stats` (Zahlen).
Fuer echte "Speicherverwaltung und Suche" muss man den Graph auch per
Freitext finden koennen — inkl. der Kanten, die ihn vom reinen Vektor-Store
unterscheiden (09-COMPANY-BRAIN.md §8, Abnahmefragen).

Bewusst kein Vektor-Index fuer den Graph: bei < 1000 Knoten reicht ILIKE ueber
Titel/Name/external_id + payload-Text; das ist deterministisch nachvollziehbar
(P4) statt "aehnlich klingend". Traverse liefert je Treffer die 1-Hop-Kanten
mit dazu, damit ein Suchergebnis direkt zeigt, WORAN ein Knoten haengt.
"""

from __future__ import annotations

import re
from typing import Any

from .db import get_connection

MAX_TOKENS = 6

# Kleine, bewusst kuratierte Stopwortliste (Frage-/Fuellwoerter DE+EN) — kein
# NLP-Modell (P4). Ziel: aus "Welche Policy gilt fuer consulting?" muss
# "policy"/"consulting" uebrig bleiben, nicht "welche"/"gilt"/"fuer".
STOPWORDS = {
    "welche", "welcher", "welches", "wer", "was", "wie", "wo", "wann", "warum",
    "ist", "sind", "war", "waren", "gilt", "gelten", "gab", "haben", "hat",
    "kann", "wird", "werden", "soll", "sollte", "muss", "duerfen",
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem",
    "und", "oder", "aber", "auch", "noch", "nicht", "nur", "schon",
    "für", "fuer", "von", "vom", "zu", "zum", "zur", "mit", "im", "in", "am",
    "auf", "aus", "bei", "über", "ueber", "unter", "durch",
    "the", "a", "an", "is", "are", "for", "of", "to", "in", "on", "with",
}


def _title_of(node_type: str, external_id: str, payload: dict[str, Any]) -> str:
    return str(payload.get("title") or payload.get("name") or external_id)


def _snippet_of(payload: dict[str, Any]) -> str:
    text = payload.get("summary") or payload.get("text") or ""
    return str(text)[:280]


def _edge_rows_to_labels(conn: Any, rows: list[dict[str, Any]], key: str) -> list[dict[str, str]]:
    """Reichert Roh-Kantenzeilen (nur IDs) um node_type/external_id/Titel an."""
    ids = [r[key] for r in rows]
    if not ids:
        return []
    lookup = {
        row["id"]: row
        for row in conn.execute(
            "SELECT id, node_type, external_id, payload FROM kg_nodes WHERE id = ANY(%s)",
            (ids,),
        ).fetchall()
    }
    out = []
    for r in rows:
        node = lookup.get(r[key])
        if node is None:
            continue
        out.append(
            {
                "edge_type": r["edge_type"],
                "node_id": str(node["id"]),
                "node_type": node["node_type"],
                "external_id": node["external_id"],
                "title": _title_of(node["node_type"], node["external_id"], node["payload"]),
            }
        )
    return out


def _tokenize(query: str) -> list[str]:
    words = re.findall(r"\w+", query.lower())
    tokens = [w for w in words if w not in STOPWORDS and len(w) >= 2]
    # Fallback: wenn nach Stopwort-Filter nichts uebrig bleibt (z.B. Frage nur
    # aus Fuellwoertern), lieber ungefiltert suchen als leer zurueckzugeben.
    return (tokens or words)[:MAX_TOKENS]


def search_nodes(
    tenant_id: str,
    query: str,
    node_types: list[str] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Freitext-Suche ueber Knoten + 1-Hop-Nachbarn je Treffer.

    Matching: OR ueber Tokens (external_id ODER payload-Text), Ranking nach
    Anzahl treffender Tokens — robust gegen natuersprachliche Fragen mit
    Fuellwoertern, ohne LLM/Embedding (P4, deterministisch nachvollziehbar).
    """
    tokens = _tokenize(query)
    if not tokens:
        return []

    where = ["tenant_id = %(tenant_id)s"]
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}
    match_conditions = []
    score_terms = []
    for i, tok in enumerate(tokens):
        key = f"tok{i}"
        params[key] = f"%{tok}%"
        cond = f"(external_id ILIKE %({key})s OR payload::text ILIKE %({key})s)"
        match_conditions.append(cond)
        score_terms.append(f"(CASE WHEN {cond} THEN 1 ELSE 0 END)")
    where.append(f"({' OR '.join(match_conditions)})")
    if node_types:
        where.append("node_type = ANY(%(node_types)s)")
        params["node_types"] = node_types

    sql = f"""
        SELECT id, node_type, external_id, payload, k_path,
               ({" + ".join(score_terms)}) AS match_score
        FROM kg_nodes
        WHERE {" AND ".join(where)}
        ORDER BY match_score DESC, updated_at DESC
        LIMIT %(limit)s
    """

    with get_connection() as conn:
        nodes = conn.execute(sql, params).fetchall()
        results = []
        for node in nodes:
            edges_out = conn.execute(
                "SELECT edge_type, to_node_id FROM kg_edges WHERE from_node_id = %s LIMIT 20",
                (node["id"],),
            ).fetchall()
            edges_in = conn.execute(
                "SELECT edge_type, from_node_id FROM kg_edges WHERE to_node_id = %s LIMIT 20",
                (node["id"],),
            ).fetchall()
            results.append(
                {
                    "id": str(node["id"]),
                    "node_type": node["node_type"],
                    "external_id": node["external_id"],
                    "title": _title_of(node["node_type"], node["external_id"], node["payload"]),
                    "snippet": _snippet_of(node["payload"]),
                    "k_path": node["k_path"],
                    "edges_out": _edge_rows_to_labels(conn, edges_out, "to_node_id"),
                    "edges_in": _edge_rows_to_labels(conn, edges_in, "from_node_id"),
                }
            )
        return results


def list_nodes(tenant_id: str, node_type: str, limit: int = 200) -> list[dict[str, Any]]:
    """Alle Knoten eines Typs, ohne Kanten (fuer die Browse-Ansicht der Console)."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, node_type, external_id, payload, k_path
            FROM kg_nodes
            WHERE tenant_id = %s AND node_type = %s
            ORDER BY external_id
            LIMIT %s
            """,
            (tenant_id, node_type, limit),
        ).fetchall()
    return [
        {
            "id": str(r["id"]),
            "node_type": r["node_type"],
            "external_id": r["external_id"],
            "title": _title_of(r["node_type"], r["external_id"], r["payload"]),
            "snippet": _snippet_of(r["payload"]),
            "k_path": r["k_path"],
        }
        for r in rows
    ]
