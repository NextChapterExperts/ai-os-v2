"""Google Drive — rekursive PDF-Inventur für Rechnungs-Backfill."""

from __future__ import annotations

from typing import Any, Iterator

from core.google import auth
from core.google.drive_client import _FOLDER_MIME
from core.google.scopes import scope_urls

_DRIVE_SCOPES = scope_urls(["drive"])


def build_drive_service(*, interactive: bool = False, credentials=None):
    from googleapiclient.discovery import build

    if credentials is not None:
        return build("drive", "v3", credentials=credentials)
    creds = auth.load_credentials(
        _DRIVE_SCOPES,
        "token.json",
        interactive=interactive,
        tool="drive.backfill",
    )
    return build("drive", "v3", credentials=creds)


def _resolve_folder_by_name(drive, segments: list[str]) -> str | None:
    parent = "root"
    for name in segments:
        safe = name.replace("'", "\\'")
        query = (
            f"name = '{safe}' and '{parent}' in parents "
            f"and mimeType = '{_FOLDER_MIME}' and trashed = false"
        )
        result = (
            drive.files()
            .list(q=query, fields="files(id,name)", pageSize=2, spaces="drive")
            .execute()
        )
        files = result.get("files", [])
        if not files:
            return None
        parent = files[0]["id"]
    return parent


def resolve_invoice_root_folder_id(
    config: dict,
    drive,
) -> tuple[str, str]:
    """Root-Ordner-ID und Anzeigename (z. B. Rechnungen)."""
    drive_cfg = config.get("drive") or {}
    root_name = str(drive_cfg.get("root_folder_name") or "Rechnungen")
    root_id = str(drive_cfg.get("root_folder_id") or "").strip()
    if root_id:
        return root_id, root_name

    resolved = _resolve_folder_by_name(drive, [root_name])
    if not resolved:
        raise FileNotFoundError(
            f"Drive-Ordner «{root_name}» nicht gefunden. "
            "Optional root_folder_id in config/invoice.yaml setzen."
        )
    return resolved, root_name


def iter_drive_pdfs(
    root_folder_id: str,
    drive,
    *,
    root_label: str = "Rechnungen",
) -> Iterator[dict[str, Any]]:
    """Alle PDFs unter root rekursiv (mit drive_path, webViewLink)."""
    stack: list[tuple[str, str]] = [(root_folder_id, root_label)]

    while stack:
        folder_id, rel_path = stack.pop()
        page_token = None
        while True:
            result = (
                drive.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    fields="nextPageToken, files(id,name,mimeType,webViewLink,modifiedTime)",
                    pageSize=200,
                    pageToken=page_token,
                )
                .execute()
            )
            for item in result.get("files", []):
                mime = item.get("mimeType") or ""
                name = item.get("name") or ""
                if mime == _FOLDER_MIME:
                    stack.append((item["id"], f"{rel_path}/{name}"))
                    continue
                if not (name.lower().endswith(".pdf") or mime == "application/pdf"):
                    continue
                yield {
                    "id": item["id"],
                    "name": name,
                    "webViewLink": item.get("webViewLink") or "",
                    "modifiedTime": item.get("modifiedTime") or "",
                    "drive_path": f"{rel_path}/{name}",
                }
            page_token = result.get("nextPageToken")
            if not page_token:
                break


def download_pdf_bytes(file_id: str, drive) -> bytes:
    return drive.files().get_media(fileId=file_id).execute()
