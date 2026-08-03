#!/usr/bin/env python3
"""Gemini-Drive-Poller — Google-Docs aus Drive-Ordner → chat-import (Phase 1b).

Port von v1 chat-agent/google-tools/scripts/chat_drive_poller.py nach V2:
- OAuth über core/google/auth.py
- Import über core.orchestrator.chat_import.import_transcript
- Konfiguration über config/chat-sources.yaml

Beispiel:
    python core/capture/gemini-drive-poller.py --json-lines \\
        --source gemini --account-id workspace \\
        --folder "AI-OS/gemini-chats"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_DEFAULT_STATE = Path(os.getenv("AIOS_MEMORY_ROOT", "/opt/ai-os/memory")) / "state" / "gemini-drive-state.json"
_CONFIG = _REPO / "config" / "chat-sources.yaml"


def _emit(json_lines: bool, payload: dict) -> None:
    if json_lines:
        print(json.dumps(payload, ensure_ascii=False), flush=True)
    else:
        t = payload.get("type")
        if t == "progress":
            print(f"  … {payload.get('message', '')}")
        elif t == "row":
            print(f"  ✅ {payload.get('title', '')}  ({payload.get('action')})")
        elif t == "done":
            print(
                f"Fertig — {payload.get('imported', 0)} importiert, "
                f"{payload.get('skipped', 0)} übersprungen"
            )
        elif t == "error":
            print(f"FEHLER: {payload.get('message', '')}", file=sys.stderr)


def _load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError):
        return {}


def _save_state(path: Path, state: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def _load_sources() -> list[dict[str, Any]]:
    import yaml

    cfg_path = Path(os.getenv("AIOS_CHAT_SOURCES", str(_CONFIG)))
    if not cfg_path.is_file():
        return []
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    return list(data.get("sources") or [])


def _source_by_id(source_id: str) -> dict[str, Any] | None:
    return next((s for s in _load_sources() if s.get("id") == source_id), None)


def _format_summary(result: dict[str, Any]) -> str:
    mode = "Dry-Run" if result.get("dry_run") else "Import"
    lines = [
        f"## Chat-Erfassung ({mode})",
        "",
        f"**{result.get('imported', 0)}** Chat(s)"
        + (f", **{result.get('skipped', 0)}** übersprungen" if result.get("skipped") else "")
        + (f" — Ordner `{result.get('folder', '–')}`" if result.get("folder") else ""),
    ]
    rows = result.get("rows") or []
    if rows:
        lines.append("")
        lines.append("### Gefundene Chats")
        for row in rows[:12]:
            title = row.get("title") or "?"
            action = row.get("action") or ""
            lines.append(f"- {title}" + (f" ({action})" if action else ""))
    return "\n".join(lines)


def run_poll(
    *,
    source_id: str = "gemini-workspace",
    dry_run: bool = True,
    timeout: int = 240,
    json_lines: bool = False,
    force: bool = False,
    tenant_id: str = "nextchapter",
) -> dict[str, Any]:
    """Drive-Poll für eine konfigurierte Quelle — von MCP drive.poll_chats genutzt."""
    del timeout  # reserviert für subprocess-Timeout in späteren Versionen

    src = _source_by_id(source_id)
    if not src:
        return {"ok": False, "error": f"Quelle '{source_id}' nicht in chat-sources.yaml"}
    if src.get("mode") != "drive_poll":
        return {
            "ok": False,
            "error": "Diese Quelle ist kein Drive-Poll (mode != drive_poll).",
            "mode": src.get("mode"),
        }

    from core.google import auth, drive_client

    token_name = str(src.get("token_name") or "token.json")
    state_path = Path(os.getenv("AIOS_GEMINI_DRIVE_STATE", str(_DEFAULT_STATE)))

    try:
        auth.load_for_tool("drive", "poll_chats", token_name=token_name, interactive=False)
    except Exception as exc:
        return {"ok": False, "error": f"Auth fehlgeschlagen: {exc}"}

    folder_id = str(src.get("drive_folder_id") or "").strip()
    folder_path = "/".join(
        src.get("drive_folder_path") or [src.get("drive_folder_name") or "Gemini Artefacts"]
    )
    if not folder_id:
        segments = [s for s in folder_path.split("/") if s.strip()]
        folder_id = drive_client.resolve_folder_by_path(segments, interactive=False)
        if not folder_id:
            return {"ok": False, "error": f"Drive-Ordner nicht gefunden: {folder_path}"}

    docs = drive_client.list_files_in_folder(folder_id, interactive=False)
    state = _load_state(state_path)
    source_key = str(src.get("source") or "gemini")
    seen = state.get(source_key, {}) if isinstance(state.get(source_key), dict) else {}

    imported = 0
    skipped = 0
    rows: list[dict[str, Any]] = []

    for meta in docs:
        fid = meta["id"]
        modified = meta.get("modifiedTime", "")
        if not drive_client.is_exportable(meta.get("mimeType", "")):
            skipped += 1
            continue
        if not force and seen.get(fid) == modified:
            skipped += 1
            continue
        try:
            text = drive_client.export_file_text(meta, interactive=False)
        except Exception as exc:
            rows.append({"type": "row", "title": meta.get("name"), "action": f"error: {exc}"})
            continue
        if not text.strip():
            rows.append({"type": "row", "title": meta.get("name"), "action": "skip-kein-text"})
            skipped += 1
            continue

        transcript = {
            "source": source_key,
            "account_id": str(src.get("account_id") or "workspace"),
            "account_email": str(src.get("account_email") or ""),
            "external_id": f"{source_key}-drive-{fid}",
            "title": meta.get("name") or fid,
            "url": meta.get("webViewLink", ""),
            "source_modified_at": modified,
            "private": bool(src.get("private")),
            "body": text,
        }

        if dry_run:
            rows.append({
                "type": "row",
                "title": transcript["title"],
                "action": "dry-run",
                "external_id": transcript["external_id"],
            })
            imported += 1
            continue

        from core.orchestrator.chat_import import import_transcript

        path = import_transcript(transcript, tenant_id=tenant_id)["path"]
        seen[fid] = modified
        imported += 1
        rows.append({
            "type": "row",
            "title": transcript["title"],
            "action": "imported",
            "path": path,
            "external_id": transcript["external_id"],
        })

    if not dry_run:
        state[source_key] = seen
        _save_state(state_path, state)

    result = {
        "ok": True,
        "source_id": source_id,
        "imported": imported,
        "skipped": skipped,
        "folder": folder_id or folder_path,
        "dry_run": dry_run,
        "rows": rows,
    }
    result["summary"] = _format_summary(result)
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="Gemini Drive-Chats → chat-import (V2)")
    p.add_argument("--source-id", default="gemini-workspace")
    p.add_argument("--source", default="gemini", help="Legacy — wird von chat-sources überschrieben")
    p.add_argument("--account-id", default="workspace")
    p.add_argument("--account-email", default="")
    p.add_argument("--folder", default="", help="Ordnerpfad (Fallback wenn keine folder-id in Config)")
    p.add_argument("--folder-id", default="")
    p.add_argument("--token-name", default="token.json")
    p.add_argument("--tenant-id", default=os.getenv("DEFAULT_TENANT", "nextchapter"))
    p.add_argument("--private", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json-lines", action="store_true")
    args = p.parse_args()

    jl = args.json_lines
    _emit(jl, {"type": "progress", "step": "poll", "message": f"Quelle {args.source_id} …"})
    result = run_poll(
        source_id=args.source_id,
        dry_run=args.dry_run,
        json_lines=jl,
        force=args.force,
        tenant_id=args.tenant_id,
    )
    if not result.get("ok"):
        _emit(jl, {"type": "error", "message": result.get("error") or "Unbekannter Fehler"})
        return 1
    for row in result.get("rows") or []:
        _emit(jl, row)
    _emit(jl, {
        "type": "done",
        "imported": result.get("imported", 0),
        "skipped": result.get("skipped", 0),
        "folder": result.get("folder"),
        "source": args.source,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
