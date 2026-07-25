"""Speicherverbrauch aller Memory-Stacks — für Console / VM-Monitoring (300 GB Budget)."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("memory_storage")

MEMORY_ROOT = Path(os.environ.get("AIOS_MEMORY_ROOT", "/opt/ai-os/memory"))
MEMORY_DB = Path(os.environ.get("AIOS_MEMORY_DB", str(MEMORY_ROOT / "memory.db")))
INGEST_INBOX = Path(os.environ.get("AIOS_INGEST_INBOX", "/opt/ai-os/ingest/inbox"))
QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
VM_DISK_PATH = os.environ.get("AIOS_VM_DISK_PATH", "/")

# Bekannte Compose-Volumes (deploy/infra.yml)
DOCKER_VOLUME_LABELS: dict[str, str] = {
    "qdrant": "deploy_qdrant_data",
    "letta": "deploy_letta_data",
    "postgres_letta": "deploy_postgres_letta_data",
    "postgres_platform": "deploy_postgres_platform_data",
    "postgres_langfuse": "deploy_postgres_langfuse_data",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_bytes(path: Path) -> int:
    try:
        return path.stat().st_size if path.is_file() else 0
    except OSError:
        return 0


def _dir_bytes(path: Path, *, max_depth: int = 8) -> tuple[int, int]:
    """Rekursive Größe + Dateianzahl (begrenzte Tiefe)."""
    if not path.exists():
        return 0, 0
    total = 0
    files = 0

    def _walk(p: Path, depth: int) -> None:
        nonlocal total, files
        if depth > max_depth:
            return
        try:
            for entry in p.iterdir():
                if entry.is_symlink():
                    continue
                if entry.is_file():
                    try:
                        total += entry.stat().st_size
                        files += 1
                    except OSError:
                        pass
                elif entry.is_dir():
                    _walk(entry, depth + 1)
        except OSError:
            pass

    _walk(path, 0)
    return total, files


def _docker_volume_sizes() -> dict[str, int]:
    """Parst `docker system df -v` für Volume-Bytes."""
    sizes: dict[str, int] = {}
    try:
        proc = subprocess.run(
            ["docker", "system", "df", "-v"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0:
            return sizes
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line.startswith("deploy_"):
                continue
            parts = re.split(r"\s+", line)
            if len(parts) < 3:
                continue
            name, size_str = parts[0], parts[-1]
            if re.match(r"[\d.]+\w*", size_str):
                sizes[name] = _parse_docker_size(size_str)
    except Exception:
        log.debug("docker system df fehlgeschlagen", exc_info=True)
    return sizes


def _parse_docker_size(raw: str) -> int:
    raw = raw.strip().upper()
    mult = 1.0
    if raw.endswith("KB"):
        mult = 1024
        raw = raw[:-2]
    elif raw.endswith("MB"):
        mult = 1024**2
        raw = raw[:-2]
    elif raw.endswith("GB"):
        mult = 1024**3
        raw = raw[:-2]
    elif raw.endswith("TB"):
        mult = 1024**4
        raw = raw[:-2]
    elif raw.endswith("B"):
        raw = raw[:-1]
    try:
        return int(float(raw) * mult)
    except ValueError:
        return 0


def _qdrant_collections() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in ("content", "raw-files"):
        try:
            req = urllib.request.Request(f"{QDRANT_URL}/collections/{name}")
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
            result = data.get("result") or {}
            out[name] = {
                "points_count": result.get("points_count", 0),
                "status": result.get("status"),
                "segments_count": result.get("segments_count"),
            }
        except Exception:
            out[name] = {"points_count": None, "status": "unreachable"}
    return out


def _sqlite_source_breakdown() -> dict[str, int]:
    import sqlite3

    if not MEMORY_DB.is_file():
        return {}
    try:
        con = sqlite3.connect(str(MEMORY_DB))
        rows = con.execute(
            "SELECT source, COUNT(*) FROM chunks GROUP BY source ORDER BY COUNT(*) DESC"
        ).fetchall()
        con.close()
        return {str(r[0]): int(r[1]) for r in rows}
    except Exception:
        return {}


def _stack(
    stack_id: str,
    label: str,
    bytes_: int,
    *,
    path: str | None = None,
    detail: str | None = None,
    status: str = "ok",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "id": stack_id,
        "label": label,
        "bytes": bytes_,
        "path": path,
        "detail": detail,
        "status": status,
    }
    if meta:
        entry["meta"] = meta
    return entry


def collect_storage_stats() -> dict[str, Any]:
    """Aggregiert Speicher aller Memory-relevanten Stacks."""
    stacks: list[dict[str, Any]] = []
    docker_sizes = _docker_volume_sizes()
    qdrant_cols = _qdrant_collections()

    # SQLite L0 episodisch
    db_main = _file_bytes(MEMORY_DB)
    db_wal = _file_bytes(MEMORY_DB.with_name(MEMORY_DB.name + "-wal"))
    db_shm = _file_bytes(MEMORY_DB.with_name(MEMORY_DB.name + "-shm"))
    sqlite_total = db_main + db_wal + db_shm
    sources = _sqlite_source_breakdown()
    stacks.append(
        _stack(
            "sqlite_episodic",
            "SQLite episodisch (L0 Capture)",
            sqlite_total,
            path=str(MEMORY_DB),
            detail=f"{sum(sources.values()) if sources else 0} Chunks",
            meta={"sources": sources, "db_bytes": db_main, "wal_bytes": db_wal, "shm_bytes": db_shm},
        )
    )

    # State (Working/Tactical, Poller, Letta-Agent-Map)
    state_dir = MEMORY_ROOT / "state"
    state_bytes, state_files = _dir_bytes(state_dir)
    stacks.append(
        _stack(
            "state_files",
            "State (Working/Tactical, Poller, Audit)",
            state_bytes,
            path=str(state_dir),
            detail=f"{state_files} Dateien",
        )
    )

    # Projekte / Cursor-Metadaten
    projects_dir = MEMORY_ROOT / "projects"
    proj_bytes, proj_files = _dir_bytes(projects_dir)
    if proj_bytes or projects_dir.exists():
        stacks.append(
            _stack(
                "memory_projects",
                "Memory-Projekte / Cursor-Metadaten",
                proj_bytes,
                path=str(projects_dir),
                detail=f"{proj_files} Dateien",
            )
        )

    # Ingest-Inbox (Gemini/Chats vor Import)
    inbox_bytes, inbox_files = _dir_bytes(INGEST_INBOX)
    stacks.append(
        _stack(
            "ingest_inbox",
            "Ingest-Inbox (Gemini/Chats)",
            inbox_bytes,
            path=str(INGEST_INBOX),
            detail=f"{inbox_files} Dateien",
            status="ok" if INGEST_INBOX.exists() else "missing",
        )
    )

    # Qdrant L1 (Docker-Volume)
    qdrant_vol = docker_sizes.get(DOCKER_VOLUME_LABELS["qdrant"], 0)
    content_pts = (qdrant_cols.get("content") or {}).get("points_count")
    raw_pts = (qdrant_cols.get("raw-files") or {}).get("points_count")
    stacks.append(
        _stack(
            "qdrant_l1",
            "Qdrant L1 (content + raw-files)",
            qdrant_vol,
            path=f"docker volume {DOCKER_VOLUME_LABELS['qdrant']}",
            detail=f"content: {content_pts or '?'} · raw-files: {raw_pts or '?'} Punkte",
            status="ok" if qdrant_vol else "unknown",
            meta={"collections": qdrant_cols},
        )
    )

    # Letta L2/L3 Agent-Runtime
    letta_vol = docker_sizes.get(DOCKER_VOLUME_LABELS["letta"], 0)
    letta_pg = docker_sizes.get(DOCKER_VOLUME_LABELS["postgres_letta"], 0)
    stacks.append(
        _stack(
            "letta_runtime",
            "Letta Agent-Runtime (L2/L3)",
            letta_vol + letta_pg,
            path=f"docker volumes {DOCKER_VOLUME_LABELS['letta']} + postgres_letta",
            detail=f"App { _fmt(letta_vol) } · Postgres { _fmt(letta_pg) }",
            meta={"letta_bytes": letta_vol, "postgres_letta_bytes": letta_pg},
        )
    )

    # Knowledge Graph (Postgres Platform)
    kg_vol = docker_sizes.get(DOCKER_VOLUME_LABELS["postgres_platform"], 0)
    stacks.append(
        _stack(
            "postgres_kg",
            "Postgres Knowledge Graph (G)",
            kg_vol,
            path=f"docker volume {DOCKER_VOLUME_LABELS['postgres_platform']}",
            detail="kg_nodes / kg_edges",
        )
    )

    # LangFuse (Observability, indirekt Memory-relevant)
    lf_vol = docker_sizes.get(DOCKER_VOLUME_LABELS["postgres_langfuse"], 0)
    stacks.append(
        _stack(
            "postgres_langfuse",
            "Postgres LangFuse (Traces)",
            lf_vol,
            path=f"docker volume {DOCKER_VOLUME_LABELS['postgres_langfuse']}",
            detail="LLM-Traces / Audit-Nebenpfad",
        )
    )

    memory_total = sum(s["bytes"] for s in stacks)
    vm = shutil.disk_usage(VM_DISK_PATH)

    return {
        "ok": True,
        "checkedAt": _now_iso(),
        "vm": {
            "path": VM_DISK_PATH,
            "totalBytes": vm.total,
            "usedBytes": vm.used,
            "freeBytes": vm.free,
            "usedPercent": round(vm.used / vm.total * 100, 1) if vm.total else 0,
        },
        "memoryStacksTotalBytes": memory_total,
        "stacks": stacks,
        "budget": {
            "vmTotalGb": round(vm.total / (1024**3), 1),
            "memoryStacksGb": round(memory_total / (1024**3), 3),
            "warningPercent": float(os.environ.get("AIOS_STORAGE_WARN_PERCENT", "70")),
            "criticalPercent": float(os.environ.get("AIOS_STORAGE_CRIT_PERCENT", "85")),
        },
    }


def _fmt(n: int) -> str:
    if n >= 1024**3:
        return f"{n / 1024**3:.2f} GB"
    if n >= 1024**2:
        return f"{n / 1024**2:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"
