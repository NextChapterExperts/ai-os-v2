"""Company Brain seed loader — Offerings / Engagements (JSON until Graph)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = Path(
    __import__("os").environ.get(
        "AIOS_BRAIN_SEED",
        str(ROOT / "customers" / "nextchapter" / "knowledge" / "seed" / "brain.json"),
    )
)


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    if not SEED_PATH.exists():
        return {"offerings": [], "engagements": [], "meetings_today": []}
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def reload_seed() -> None:
    _load.cache_clear()


def list_offerings() -> list[dict[str, Any]]:
    return list(_load().get("offerings", []))


def list_engagements(status: str | None = None) -> list[dict[str, Any]]:
    items = list(_load().get("engagements", []))
    if status:
        items = [e for e in items if e.get("status") == status]
    return items


def active_engagements() -> list[dict[str, Any]]:
    return [
        e
        for e in list_engagements()
        if e.get("status") in {"pipeline", "active"}
    ]


def meetings_today() -> list[dict[str, Any]]:
    return list(_load().get("meetings_today", []))


def offering_by_id(offering_id: str) -> dict[str, Any] | None:
    for o in list_offerings():
        if o.get("id") == offering_id:
            return o
    return None


def list_people(tenant_id: str = "nextchapter") -> list[dict[str, Any]]:
    """Gibt alle Personen des Tenants aus dem Knowledge Graph und brain.json Seed zurück."""
    people_map: dict[str, dict[str, Any]] = {}

    # 1. Seed People laden
    for p in _load().get("people", []):
        people_map[p["id"]] = dict(p)

    # 2. Knowledge Graph org:Person Einpflegen
    try:
        from .kg_search import list_nodes

        nodes = list_nodes(tenant_id, "org:Person", limit=50)
        for n in nodes:
            pid = n.get("external_id") or n["id"]
            if pid not in people_map:
                people_map[pid] = {
                    "id": pid,
                    "name": n.get("title") or pid,
                    "email": (n.get("payload") or {}).get("email") or "",
                    "role": (n.get("payload") or {}).get("role") or "Member",
                }
    except Exception:
        pass

    return list(people_map.values())
