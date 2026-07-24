"""mail_triage intent — uses MCP mail stub until real IMAP/MCP is wired."""

from __future__ import annotations

from typing import Any

from ..mcp_clients import mail_stub


async def run(
    context_bundle: dict[str, Any],
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    mail = await mail_stub.list_open_actions(tenant_id)
    actions = mail.get("actions", [])
    if not actions:
        answer = (
            "Mail-MCP ist als Stub aktiv — noch keine echte Inbox angebunden.\n"
            f"{mail.get('status_note', '')}"
        )
    else:
        lines = "\n".join(
            f"• **{a.get('subject')}** — {a.get('action')}" for a in actions
        )
        answer = f"Mail-Triage (Stub):\n{lines}\n\n{mail.get('status_note', '')}"

    return {
        "kind": "ask",
        "answer": answer.strip(),
        "mode": "mail_triage",
        "detail": False,
        "model": "mail-mcp-stub",
        "sources": [
            {
                "id": a.get("id", f"mail-{i}"),
                "role": "mail",
                "title": a.get("subject", ""),
                "snippet": a.get("action", ""),
                "chat_id": "",
                "source": "mcp-mail-stub",
                "ingested_at": "",
            }
            for i, a in enumerate(actions)
        ],
        "sourceCount": len(actions),
        "mail_stub": mail.get("status"),
        "tenant_id": tenant_id,
    }
