"""E-Mail / Rechnungs-Pipeline — Status & Ausführung (MCP-native)."""

from __future__ import annotations

from typing import Any

import core.mcp_gateway.adapters  # noqa: F401 — Handler registrieren
from core.google.invoice.config import load_invoice_config, invoice_config_path
from core.mcp_gateway.adapters.registry import dispatch as mcp_dispatch


def invoice_status(tenant_id: str = "nextchapter") -> dict[str, Any]:
    """Google-OAuth + Invoice-Konfiguration (ohne Gmail-Scan)."""
    mail = mcp_dispatch("mail", "status", {"tenant_id": tenant_id})
    cfg = load_invoice_config(tenant_id)
    spreadsheet_id = str(cfg.get("spreadsheet_id") or "")
    drive_root = str((cfg.get("drive") or {}).get("root_folder_name") or "Rechnungen")
    drive_folder_id = str((cfg.get("drive") or {}).get("root_folder_id") or "")
    drive_folder_url = ""
    if drive_folder_id:
        drive_folder_url = f"https://drive.google.com/drive/folders/{drive_folder_id}"
    else:
        try:
            from core.google import drive_client

            resolved_id = drive_client.resolve_folder_by_path([drive_root], interactive=False)
            if resolved_id:
                drive_folder_id = resolved_id
                drive_folder_url = f"https://drive.google.com/drive/folders/{resolved_id}"
        except Exception:
            pass
    return {
        "ok": mail.get("ok", False),
        "tenant_id": tenant_id,
        "google": mail.get("google") or {},
        "status": mail.get("status", "unknown"),
        "config_path": str(invoice_config_path(tenant_id)),
        "spreadsheet_id": spreadsheet_id,
        "sheet_name": str(cfg.get("sheet_name") or "Übersicht"),
        "sheet_url": (
            f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            if spreadsheet_id
            else ""
        ),
        "drive_root": drive_root,
        "drive_folder_id": drive_folder_id,
        "drive_folder_url": drive_folder_url,
        "processed_label": str((cfg.get("gmail") or {}).get("processed_label") or "R-Verarbeitet"),
    }


def invoice_preview(tenant_id: str = "nextchapter") -> dict[str, Any]:
    """Gmail-Scan — nur Lesen, kein Sheet/Drive-Schreiben."""
    return mcp_dispatch("mail", "preview_invoices", {"tenant_id": tenant_id})


async def invoice_run(
    tenant_id: str,
    *,
    dry_run: bool = True,
    skip_archive: bool = False,
) -> dict[str, Any]:
    """Volle Pipeline über email-agent (MCP-only)."""
    from core.orchestrator.handlers import invoice_pipeline

    return await invoice_pipeline.run_invoice_pipeline(
        {},
        tenant_id,
        {"dry_run": dry_run, "skip_archive": skip_archive},
    )
