"""DP-Service — Company-Brain-Commit-Pfad.

Implementiert `POST /v1/dataproduct/commit` (siehe server.py) fuer die
org:*-DataProducts aus dataproducts.py: Schema ist durch die Pydantic-Klasse
bereits validiert; hier folgt die atomare Persistenz nach
docs/09-COMPANY-BRAIN.md §12.3 (K-Pfad pruefen -> kg_nodes upsert ->
kg_edges upsert -> Audit-Hash-Chain), alles in einer Postgres-Transaktion.

Kein Fach-/Platform-Agent ruft dieses Modul direkt — nur ueber den HTTP-
Endpoint, damit `kg.upsert_*` ausschliesslich beim DP-Service liegt (P15).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataproducts import (
    NODE_TYPE_BY_CLASS,
    DataProduct,
    OrgClaim,
    OrgDecision,
    OrgEngagement,
    OrgKnowledgeAsset,
    OrgMeeting,
    OrgPolicy,
)
from .db import get_connection

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJEKTE_ROOT = REPO_ROOT.parent  # ~/Projekte — Geschwister-Repo (active/*)


class DPCommitError(Exception):
    pass


def _node_type_and_external_id(dp: DataProduct) -> tuple[str, str]:
    cls = type(dp)
    if cls in NODE_TYPE_BY_CLASS:
        node_type, id_field = NODE_TYPE_BY_CLASS[cls]
        return node_type, getattr(dp, id_field)
    
    # Fallback für SDK/Custom DataProducts
    node_type = getattr(cls, "node_type", f"custom:{cls.__name__}")
    id_val = getattr(dp, "dp_id", getattr(dp, "id", None))
    if id_val is None:
        raise DPCommitError(f"Unbekannter DataProduct-Typ ohne ID: {cls.__name__}")
    return node_type, str(id_val)


def _ingest_recommended(dp: DataProduct) -> bool:
    if isinstance(dp, OrgKnowledgeAsset):
        return dp.published
    return dp.ingest_recommended


def resolve_k_path(path: str) -> Path | None:
    """K-Datei relativ zum AI-OS-Repo ODER relativ zu Projekte/ (Front-Door-
    READMEs unter active/* liegen im Geschwister-Repo, nicht in diesem)."""
    for candidate in (REPO_ROOT / path, PROJEKTE_ROOT / path):
        if candidate.exists():
            return candidate
    return None


def _edges_for(dp: DataProduct) -> list[tuple[str, str, str]]:
    """(edge_type, direction, ref) — direction 'out': dp -> ref, 'in': ref -> dp."""
    edges: list[tuple[str, str, str]] = []
    if isinstance(dp, OrgEngagement):
        if dp.offering_ref:
            edges.append(("about", "out", dp.offering_ref))
        if dp.org_ref:
            edges.append(("about", "out", dp.org_ref))
    elif isinstance(dp, OrgMeeting):
        edges += [("attended_by", "out", ref) for ref in dp.attendee_refs]
        edges += [("about", "out", ref) for ref in dp.about_refs]
    elif isinstance(dp, OrgDecision):
        edges += [("about", "out", ref) for ref in dp.about_refs]
        if dp.meeting_ref:
            edges.append(("decided_in", "out", dp.meeting_ref))
        if dp.supersedes_ref:
            edges.append(("supersedes", "out", dp.supersedes_ref))
    elif isinstance(dp, OrgPolicy):
        edges += [("applies_to", "out", ref) for ref in dp.applies_to_refs]
    elif isinstance(dp, OrgKnowledgeAsset):
        edges += [("documents", "out", ref) for ref in dp.documents_refs]
    elif isinstance(dp, OrgClaim):
        if dp.asserts_from_ref:
            edges.append(("asserts", "in", dp.asserts_from_ref))
        edges += [("supports", "out", ref) for ref in dp.supports_refs]
    return edges


def _hash_entry(prev_hash: str | None, payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(((prev_hash or "") + canonical).encode("utf-8")).hexdigest()


def commit_dataproduct(dp: DataProduct, dry_run: bool = False) -> dict[str, Any]:
    node_type, external_id = _node_type_and_external_id(dp)
    payload = dp.model_dump(
        mode="json", exclude={"tenant_id", "produced_by", "workflow_run_id"}
    )

    k_path_str: str | None = getattr(dp, "path", None)
    storage_target = getattr(dp, "storage_target", ["G"])
    if "K" in storage_target and k_path_str:
        if resolve_k_path(k_path_str) is None:
            payload["_k_path_unresolved"] = True

    if dry_run:
        return {
            "node_id": None,
            "node_type": node_type,
            "external_id": external_id,
            "ingest_queued": _ingest_recommended(dp),
            "dry_run": True,
        }

    edges = _edges_for(dp)
    edges_created = 0
    edges_skipped: list[str] = []

    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO kg_nodes (tenant_id, node_type, external_id, payload, k_path, produced_by)
            VALUES (%(tenant_id)s, %(node_type)s, %(external_id)s, %(payload)s, %(k_path)s, %(produced_by)s)
            ON CONFLICT (tenant_id, node_type, external_id)
            DO UPDATE SET payload = EXCLUDED.payload, k_path = EXCLUDED.k_path,
                          produced_by = EXCLUDED.produced_by, updated_at = NOW()
            RETURNING id
            """,
            {
                "tenant_id": dp.tenant_id,
                "node_type": node_type,
                "external_id": external_id,
                "payload": json.dumps(payload, default=str, ensure_ascii=False),
                "k_path": k_path_str,
                "produced_by": dp.produced_by,
            },
        ).fetchone()
        node_id = row["id"]

        for edge_type, direction, ref in edges:
            target = conn.execute(
                "SELECT id FROM kg_nodes WHERE tenant_id = %s AND external_id = %s",
                (dp.tenant_id, ref),
            ).fetchone()
            if target is None:
                edges_skipped.append(f"{edge_type}->{ref}")
                continue
            from_id, to_id = (
                (node_id, target["id"]) if direction == "out" else (target["id"], node_id)
            )
            conn.execute(
                """
                INSERT INTO kg_edges (tenant_id, edge_type, from_node_id, to_node_id, produced_by)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, edge_type, from_node_id, to_node_id) DO NOTHING
                """,
                (dp.tenant_id, edge_type, from_id, to_id, dp.produced_by),
            )
            edges_created += 1

        prev = conn.execute(
            "SELECT entry_hash FROM ai_os_log WHERE tenant_id = %s ORDER BY created_at DESC LIMIT 1",
            (dp.tenant_id,),
        ).fetchone()
        prev_hash = prev["entry_hash"] if prev else None
        audit_payload = {
            "event": "dp_commit",
            "node_type": node_type,
            "external_id": external_id,
            "node_id": str(node_id),
            "produced_by": dp.produced_by,
            "workflow_run_id": dp.workflow_run_id,
            "edges_created": edges_created,
            "edges_skipped": edges_skipped,
        }
        entry_hash = _hash_entry(prev_hash, audit_payload)
        conn.execute(
            """
            INSERT INTO ai_os_log (tenant_id, event_type, payload, prev_hash, entry_hash)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                dp.tenant_id,
                "dp_commit",
                json.dumps(audit_payload, ensure_ascii=False),
                prev_hash,
                entry_hash,
            ),
        )
        # kein explizites conn.commit(): der `with`-Block committet automatisch
        # am Ende (oder rollt zurueck bei Exception) - eine Transaktion fuer
        # Node + Edges + Audit (P18 atomarer Commit).

    return {
        "node_id": str(node_id),
        "node_type": node_type,
        "external_id": external_id,
        "ingest_queued": _ingest_recommended(dp),
        "edges_created": edges_created,
        "edges_skipped": edges_skipped,
        "dry_run": False,
    }


def kg_stats(tenant_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        nodes = conn.execute(
            "SELECT node_type, COUNT(*) AS n FROM kg_nodes WHERE tenant_id = %s "
            "GROUP BY node_type ORDER BY node_type",
            (tenant_id,),
        ).fetchall()
        edges = conn.execute(
            "SELECT edge_type, COUNT(*) AS n FROM kg_edges WHERE tenant_id = %s "
            "GROUP BY edge_type ORDER BY edge_type",
            (tenant_id,),
        ).fetchall()
        total_nodes = conn.execute(
            "SELECT COUNT(*) AS n FROM kg_nodes WHERE tenant_id = %s", (tenant_id,)
        ).fetchone()["n"]
        total_edges = conn.execute(
            "SELECT COUNT(*) AS n FROM kg_edges WHERE tenant_id = %s", (tenant_id,)
        ).fetchone()["n"]
    return {
        "tenant_id": tenant_id,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "nodes_by_type": {r["node_type"]: r["n"] for r in nodes},
        "edges_by_type": {r["edge_type"]: r["n"] for r in edges},
    }


def resolve_node_by_id(tenant_id: str, node_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        node = conn.execute(
            "SELECT * FROM kg_nodes WHERE tenant_id = %s AND id = %s",
            (tenant_id, node_id),
        ).fetchone()
        if node is None:
            return None
        edges_out = conn.execute(
            """
            SELECT e.edge_type, n.id AS node_id, n.node_type, n.external_id, n.payload
            FROM kg_edges e JOIN kg_nodes n ON n.id = e.to_node_id
            WHERE e.from_node_id = %s
            """,
            (node["id"],),
        ).fetchall()
        edges_in = conn.execute(
            """
            SELECT e.edge_type, n.id AS node_id, n.node_type, n.external_id, n.payload
            FROM kg_edges e JOIN kg_nodes n ON n.id = e.from_node_id
            WHERE e.to_node_id = %s
            """,
            (node["id"],),
        ).fetchall()

    def _label(row: dict[str, Any]) -> dict[str, Any]:
        payload = row["payload"] or {}
        title = payload.get("title") or payload.get("name") or row["external_id"]
        return {
            "edge_type": row["edge_type"],
            "to": str(row["node_id"]),
            "from": str(row["node_id"]),
            "node_type": row["node_type"],
            "external_id": row["external_id"],
            "title": title,
        }

    return {
        "id": str(node["id"]),
        "node_type": node["node_type"],
        "external_id": node["external_id"],
        "payload": node["payload"],
        "k_path": node["k_path"],
        "edges_out": [_label(e) for e in edges_out],
        "edges_in": [_label(e) for e in edges_in],
    }
