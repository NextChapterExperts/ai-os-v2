"""Gmail — Lesen und Header-Parsing für MCP mail-Adapter."""

from __future__ import annotations

import base64
from typing import Any

from . import auth

DEFAULT_PROCESSED_LABEL = "R-Verarbeitet"
GMAIL_MODIFY_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def _service(*, tool: str = "get_recent", interactive: bool = False):
    from googleapiclient.discovery import build

    creds = auth.load_for_tool("mail", tool, interactive=interactive)
    return build("gmail", "v1", credentials=creds)


def _modify_service(*, interactive: bool = False):
    from googleapiclient.discovery import build

    creds = auth.load_credentials(GMAIL_MODIFY_SCOPES, "token_gmail_modify.json", interactive=interactive)
    return build("gmail", "v1", credentials=creds)


def _header_map(payload: dict[str, Any]) -> dict[str, str]:
    headers = payload.get("headers") or []
    out: dict[str, str] = {}
    for h in headers:
        name = (h.get("name") or "").lower()
        if name:
            out[name] = h.get("value") or ""
    return out


def list_messages(
    *,
    max_results: int = 20,
    query: str = "",
    only_unseen: bool = False,
    interactive: bool = False,
) -> list[dict[str, Any]]:
    svc = _service(interactive=interactive)
    q = query.strip()
    if only_unseen:
        q = f"{q} is:unread".strip()
    params: dict[str, Any] = {"userId": "me", "maxResults": max(1, min(max_results, 50))}
    if q:
        params["q"] = q
    results = svc.users().messages().list(**params).execute()
    messages = results.get("messages") or []
    out: list[dict[str, Any]] = []
    for idx, msg_ref in enumerate(messages):
        msg = svc.users().messages().get(userId="me", id=msg_ref["id"], format="metadata").execute()
        headers = _header_map(msg.get("payload") or {})
        out.append({
            "index": idx,
            "id": msg_ref["id"],
            "thread_id": msg.get("threadId") or "",
            "subject": headers.get("subject", "(Kein Betreff)"),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "date": headers.get("date", ""),
            "snippet": msg.get("snippet") or "",
            "label_ids": msg.get("labelIds") or [],
        })
    return out


def get_message(message_id: str, *, interactive: bool = False) -> dict[str, Any]:
    svc = _service(tool="get_by_id", interactive=interactive)
    msg = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = _header_map(msg.get("payload") or {})
    body = _extract_body(msg.get("payload") or {})
    return {
        "id": message_id,
        "thread_id": msg.get("threadId") or "",
        "subject": headers.get("subject", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "date": headers.get("date", ""),
        "snippet": msg.get("snippet") or "",
        "body": body[:8000],
        "headers": headers,
    }


def _extract_body(payload: dict[str, Any]) -> str:
    if payload.get("body", {}).get("data"):
        return _decode_b64(payload["body"]["data"])
    parts = payload.get("parts") or []
    for part in parts:
        mime = part.get("mimeType") or ""
        if mime == "text/plain" and part.get("body", {}).get("data"):
            return _decode_b64(part["body"]["data"])
    for part in parts:
        nested = _extract_body(part)
        if nested:
            return nested
    return ""


def _decode_b64(data: str) -> str:
    try:
        raw = base64.urlsafe_b64decode(data + "==")
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def parse_headers_from_message(message_id: str, *, interactive: bool = False) -> dict[str, Any]:
    msg = get_message(message_id, interactive=interactive)
    return {
        "id": msg["id"],
        "from": msg["from"],
        "to": msg["to"],
        "cc": msg.get("cc") or "",
        "subject": msg["subject"],
        "date": msg["date"],
    }


def resolve_label_id(gmail_service, label_name: str) -> str | None:
    labels = gmail_service.users().labels().list(userId="me").execute().get("labels", [])
    for label in labels:
        if label["name"].casefold() == label_name.casefold():
            return label["id"]
    return None


def is_message_processed(message: dict, processed_label_id: str | None) -> bool:
    if not processed_label_id:
        return False
    return processed_label_id in (message.get("labelIds") or [])


def get_or_create_label(gmail_service, label_name: str) -> str:
    existing = resolve_label_id(gmail_service, label_name)
    if existing:
        return existing
    created = (
        gmail_service.users()
        .labels()
        .create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )
        .execute()
    )
    return created["id"]


def mark_messages_processed(
    message_ids: list[str],
    *,
    label_name: str = DEFAULT_PROCESSED_LABEL,
    interactive: bool = False,
) -> int:
    unique = list(dict.fromkeys(mid for mid in message_ids if mid))
    if not unique:
        return 0
    svc = _modify_service(interactive=interactive)
    label_id = get_or_create_label(svc, label_name)
    labeled = 0
    batch_size = 1000
    for start in range(0, len(unique), batch_size):
        chunk = unique[start : start + batch_size]
        svc.users().messages().batchModify(
            userId="me",
            body={"ids": chunk, "addLabelIds": [label_id], "removeLabelIds": []},
        ).execute()
        labeled += len(chunk)
    return labeled
