"""Google Drive — Ordner-Auflösung und Text-Export (Gemini-Chats)."""

from __future__ import annotations

import re
from typing import Any

from . import auth

_GDOC_MIME = "application/vnd.google-apps.document"
_FOLDER_MIME = "application/vnd.google-apps.folder"
_CTRL_KEEP = {"\n", "\t"}
_TEXT_RUN = re.compile(r"[^\x00-\x08\x0b\x0c\x0e-\x1f\ufffd]{3,}")


def _service(*, tool: str = "list_folder", interactive: bool = False):
    from googleapiclient.discovery import build

    creds = auth.load_for_tool("drive", tool, interactive=interactive)
    return build("drive", "v3", credentials=creds)


def resolve_folder_by_path(segments: list[str], *, interactive: bool = False) -> str | None:
    drive = _service(interactive=interactive)
    parent = "root"
    for name in segments:
        safe = name.replace("'", "\\'")
        q = (
            f"name = '{safe}' and '{parent}' in parents "
            f"and mimeType = '{_FOLDER_MIME}' and trashed = false"
        )
        res = drive.files().list(q=q, fields="files(id,name)", pageSize=2, spaces="drive").execute()
        files = res.get("files", [])
        if not files:
            return None
        parent = files[0]["id"]
    return parent


def list_files_in_folder(folder_id: str, *, interactive: bool = False) -> list[dict[str, Any]]:
    drive = _service(interactive=interactive)
    out: list[dict[str, Any]] = []
    page_token = None
    while True:
        res = drive.files().list(
            q=(f"'{folder_id}' in parents and trashed = false "
               f"and mimeType != '{_FOLDER_MIME}'"),
            fields="nextPageToken, files(id,name,mimeType,modifiedTime,webViewLink)",
            pageSize=200,
            pageToken=page_token,
        ).execute()
        out.extend(res.get("files", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return out


def _is_exportable(mime: str) -> bool:
    if mime == _GDOC_MIME:
        return True
    return not mime.startswith("application/vnd.google-apps.")


def _clean_text(text: str) -> str:
    text = text.replace("\ufffd", "")
    cleaned = "".join(ch for ch in text if ch in _CTRL_KEEP or ord(ch) >= 32)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _looks_like_text(raw: str) -> bool:
    if not raw:
        return False
    non_printable = sum(
        1 for ch in raw if (ch not in _CTRL_KEEP and ord(ch) < 32) or ch == "\ufffd"
    )
    return (non_printable / max(len(raw), 1)) < 0.30


def _extract_readable(raw: str) -> str:
    runs = _TEXT_RUN.findall(raw.replace("\ufffd", ""))
    keep = [
        r.strip() for r in runs
        if sum(ch.isalpha() or ch.isspace() for ch in r) >= max(3, len(r) * 0.5)
    ]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(keep)).strip()


def export_file_text(file_meta: dict[str, Any], *, interactive: bool = False) -> str:
    drive = _service(tool="export_document", interactive=interactive)
    mime = file_meta.get("mimeType", "")
    fid = file_meta["id"]
    if mime == _GDOC_MIME:
        data = drive.files().export(fileId=fid, mimeType="text/plain").execute()
        raw = data.decode("utf-8", "replace") if isinstance(data, bytes) else str(data)
        return _clean_text(raw)
    data = drive.files().get_media(fileId=fid).execute()
    raw = data.decode("utf-8", "replace") if isinstance(data, bytes) else str(data)
    if mime.startswith("application/vnd.google-") or not _looks_like_text(raw):
        return _extract_readable(raw)
    return _clean_text(raw)


def is_exportable(mime: str) -> bool:
    return _is_exportable(mime)
