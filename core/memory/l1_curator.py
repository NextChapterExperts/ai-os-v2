"""L1-Curator — Qdrant `content` Collection: Stats, Dedup, Rolling Retention.

Pipeline (docs/10-MEMORY-EINFACH.md §7):
  Nur kuratierte/published Inhalte (Ingest-Agent → Qdrant `content`).
  Kein Roh-Chat. Rolling 90 Tage via `ingested_at` im Payload.

Modi:
  stats          — Punktanzahl, Assets, älteste/neueste Ingestion
  exact_dedup    — identischer `text`-Hash → ein Punkt behalten
  semantic_dedup — Cosine ≥ Schwellwert → Cluster, ein Punkt behalten
  rolling        — Punkte älter als retention_days löschen
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

log = logging.getLogger("l1_curator")

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "memory-curator.yaml"

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
CONTENT_COLLECTION = os.environ.get("QDRANT_COLLECTION_CONTENT", "content")
SCROLL_BATCH = int(os.environ.get("L1_CURATOR_SCROLL_BATCH", "256"))


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    if CONFIG_PATH.is_file():
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _cfg(key: str, default: Any) -> Any:
    return _load_config().get(key, default)


def _get_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def _collection_exists(client: QdrantClient) -> bool:
    names = {c.name for c in client.get_collections().collections}
    return CONTENT_COLLECTION in names


def _parse_ingested_at(payload: dict[str, Any]) -> datetime | None:
    raw = payload.get("ingested_at")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except ValueError:
        return None


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _scroll_all(
    client: QdrantClient,
    *,
    with_vectors: bool = False,
) -> list[qm.Record]:
    if not _collection_exists(client):
        return []
    records: list[qm.Record] = []
    offset = None
    while True:
        batch, offset = client.scroll(
            collection_name=CONTENT_COLLECTION,
            limit=SCROLL_BATCH,
            offset=offset,
            with_payload=True,
            with_vectors=with_vectors,
        )
        records.extend(batch)
        if offset is None:
            break
    return records


def scan_stats(client: QdrantClient | None = None) -> dict[str, Any]:
    """Statistik über die L1-Collection `content`."""
    client = client or _get_client()
    if not _collection_exists(client):
        return {
            "ok": True,
            "collection": CONTENT_COLLECTION,
            "exists": False,
            "total_points": 0,
            "unique_assets": 0,
            "oldest_ingested_at": None,
            "newest_ingested_at": None,
        }

    records = _scroll_all(client, with_vectors=False)
    by_asset: dict[str, int] = {}
    ingested: list[datetime] = []
    for rec in records:
        payload = rec.payload or {}
        asset_id = str(payload.get("asset_id") or "unknown")
        by_asset[asset_id] = by_asset.get(asset_id, 0) + 1
        ts = _parse_ingested_at(payload)
        if ts is not None:
            ingested.append(ts)

    oldest = min(ingested).isoformat(timespec="seconds") if ingested else None
    newest = max(ingested).isoformat(timespec="seconds") if ingested else None
    return {
        "ok": True,
        "collection": CONTENT_COLLECTION,
        "exists": True,
        "total_points": len(records),
        "unique_assets": len(by_asset),
        "top_assets": sorted(by_asset.items(), key=lambda x: x[1], reverse=True)[:10],
        "oldest_ingested_at": oldest,
        "newest_ingested_at": newest,
    }


def exact_dedup(
    client: QdrantClient | None = None,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Entfernt exakte Text-Duplikate (behält neuestes ingested_at)."""
    client = client or _get_client()
    if not _collection_exists(client):
        return {"ok": True, "mode": "exact_dedup", "removed": 0, "groups": 0}

    records = _scroll_all(client, with_vectors=False)
    groups: dict[str, list[tuple[str, datetime | None]]] = {}
    for rec in records:
        payload = rec.payload or {}
        text = str(payload.get("text") or "").strip()
        if not text:
            continue
        h = _text_hash(text)
        groups.setdefault(h, []).append((str(rec.id), _parse_ingested_at(payload)))

    to_delete: list[str] = []
    dup_groups = 0
    for _h, items in groups.items():
        if len(items) < 2:
            continue
        dup_groups += 1
        items.sort(key=lambda x: x[1] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        to_delete.extend(pid for pid, _ in items[1:])

    if to_delete and not dry_run:
        client.delete(
            collection_name=CONTENT_COLLECTION,
            points_selector=qm.PointIdsList(points=to_delete),
        )

    return {
        "ok": True,
        "mode": "exact_dedup",
        "dry_run": dry_run,
        "groups": dup_groups,
        "removed": len(to_delete),
    }


def semantic_dedup(
    client: QdrantClient | None = None,
    *,
    dry_run: bool = False,
    threshold: float | None = None,
) -> dict[str, Any]:
    """Entfernt semantisch nahe Duplikate (Cosine ≥ threshold)."""
    client = client or _get_client()
    threshold = threshold if threshold is not None else float(_cfg("l1_semantic_dedup_threshold", 0.98))
    if not _collection_exists(client):
        return {"ok": True, "mode": "semantic_dedup", "removed": 0, "clusters": 0}

    records = _scroll_all(client, with_vectors=True)
    if len(records) < 2:
        return {"ok": True, "mode": "semantic_dedup", "removed": 0, "clusters": 0}

    # Sortiere stabil: neuestes ingested_at zuerst → bleibt als Repräsentant
    def _sort_key(rec: qm.Record) -> datetime:
        ts = _parse_ingested_at(rec.payload or {})
        return ts or datetime.min.replace(tzinfo=timezone.utc)

    records.sort(key=_sort_key, reverse=True)
    removed: set[str] = set()
    clusters = 0

    for i, rec in enumerate(records):
        pid = str(rec.id)
        if pid in removed or rec.vector is None:
            continue
        try:
            hits = client.query_points(
                collection_name=CONTENT_COLLECTION,
                query=rec.vector,
                limit=20,
                score_threshold=threshold,
                with_payload=False,
            ).points
        except Exception:
            log.exception("semantic_dedup query fehlgeschlagen für %s", pid)
            continue

        cluster_ids = [str(h.id) for h in hits if str(h.id) != pid]
        if not cluster_ids:
            continue
        clusters += 1
        for cid in cluster_ids:
            removed.add(cid)

    to_delete = sorted(removed)
    if to_delete and not dry_run:
        client.delete(
            collection_name=CONTENT_COLLECTION,
            points_selector=qm.PointIdsList(points=to_delete),
        )

    return {
        "ok": True,
        "mode": "semantic_dedup",
        "dry_run": dry_run,
        "threshold": threshold,
        "clusters": clusters,
        "removed": len(to_delete),
    }


def rolling_retention(
    client: QdrantClient | None = None,
    *,
    dry_run: bool = False,
    retention_days: int | None = None,
) -> dict[str, Any]:
    """Löscht Punkte älter als retention_days (Payload-Feld ingested_at)."""
    client = client or _get_client()
    retention_days = retention_days if retention_days is not None else int(_cfg("l1_retention_days", 90))
    if not _collection_exists(client):
        return {"ok": True, "mode": "rolling", "removed": 0}

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%S")
    records = _scroll_all(client, with_vectors=False)
    to_delete: list[str] = []
    for rec in records:
        payload = rec.payload or {}
        ts = _parse_ingested_at(payload)
        if ts is None:
            continue
        if ts.replace(tzinfo=timezone.utc) < cutoff:
            to_delete.append(str(rec.id))

    if to_delete and not dry_run:
        # Batchweise löschen (Qdrant limit)
        batch_size = 512
        for i in range(0, len(to_delete), batch_size):
            chunk = to_delete[i : i + batch_size]
            client.delete(
                collection_name=CONTENT_COLLECTION,
                points_selector=qm.PointIdsList(points=chunk),
            )

    return {
        "ok": True,
        "mode": "rolling",
        "dry_run": dry_run,
        "retention_days": retention_days,
        "cutoff": cutoff_str,
        "removed": len(to_delete),
    }


def run_l1_curate(
    *,
    modes: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Führt gewählte L1-Curator-Modi aus (Default: alle)."""
    modes = modes or ["stats", "exact_dedup", "semantic_dedup", "rolling"]
    client = _get_client()
    results: dict[str, Any] = {"ok": True, "dry_run": dry_run, "modes": {}}

    for mode in modes:
        if mode == "stats":
            results["modes"]["stats"] = scan_stats(client)
        elif mode == "exact_dedup":
            results["modes"]["exact_dedup"] = exact_dedup(client, dry_run=dry_run)
        elif mode == "semantic_dedup":
            results["modes"]["semantic_dedup"] = semantic_dedup(client, dry_run=dry_run)
        elif mode == "rolling":
            results["modes"]["rolling"] = rolling_retention(client, dry_run=dry_run)
        else:
            results["modes"][mode] = {"ok": False, "error": f"Unbekannter Modus: {mode}"}
            results["ok"] = False

    return results
