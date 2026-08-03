"""MCP drive-Adapter — Gemini-Chat-Erfassung über Google Drive."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from core.google import auth as google_auth
from core.mcp_gateway.adapters.registry import register

_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "chat-sources.yaml"


def _load_sources() -> list[dict[str, Any]]:
    path = Path(os.getenv("AIOS_CHAT_SOURCES", str(_CONFIG_PATH)))
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError:
        return []
    return list(data.get("sources") or [])


@register("drive", "list_sources")
def drive_list_sources(args: dict[str, Any]) -> dict[str, Any]:
    if args.get("dry_run"):
        return {
            "ok": True,
            "dry_run": True,
            "sources": [{"id": "gemini-workspace", "mode": "drive_poll"}],
        }
    return {
        "ok": True,
        "sources": _load_sources(),
        "google_ok": google_auth.token_path().is_file(),
        "poller_ready": True,
        "config_path": str(_CONFIG_PATH),
    }


@register("drive", "poll_chats")
def drive_poll_chats(args: dict[str, Any]) -> dict[str, Any]:
    source_id = str(args.get("source_id") or args.get("source") or "gemini-workspace")
    dry_run = bool(args.get("dry_run"))
    if args.get("dry_run") is None and not args.get("import"):
        dry_run = True

    if dry_run and not args.get("live"):
        return {
            "ok": True,
            "dry_run": True,
            "source_id": source_id,
            "imported": 0,
            "skipped": 0,
            "summary": "[Dry-Run] Drive-Poll simuliert — kein Import.",
            "rows": [],
        }

    from core.capture.gemini_drive_poller import run_poll

    timeout = int(args.get("timeout") or 240)
    result = run_poll(source_id=source_id, dry_run=dry_run, timeout=timeout)
    if not result.get("ok"):
        return {
            "ok": False,
            "error": result.get("error") or "poll_failed",
            "message": str(result.get("error") or result.get("message") or ""),
            **{k: v for k, v in result.items() if k not in ("ok", "error")},
        }
    return {
        "ok": True,
        "source_id": source_id,
        "dry_run": dry_run,
        "imported": result.get("imported", 0),
        "skipped": result.get("skipped", 0),
        "folder": result.get("folder"),
        "summary": result.get("summary") or "",
        "rows": result.get("rows") or [],
    }


@register("drive", "list_folder")
def drive_list_folder(args: dict[str, Any]) -> dict[str, Any]:
    from core.google import drive_client

    folder_id = args.get("folder_id")
    folder_path = args.get("folder") or args.get("path")
    if not folder_id and not folder_path:
        return {"ok": False, "error": "missing_folder", "message": "folder_id oder folder/path erforderlich"}
    if not folder_id:
        segments = [s for s in str(folder_path).split("/") if s.strip()]
        folder_id = drive_client.resolve_folder_by_path(segments, interactive=False)
        if not folder_id:
            return {"ok": False, "error": "not_found", "message": f"Ordner nicht gefunden: {folder_path}"}
    files = drive_client.list_files_in_folder(str(folder_id), interactive=False)
    return {"ok": True, "folder_id": folder_id, "files": files, "count": len(files)}
