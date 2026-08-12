"""MCP mail-Adapter — Gmail über core/google."""

from __future__ import annotations

from typing import Any

from core.google import auth as google_auth
from core.google import gmail_client
from core.mcp_gateway.adapters.registry import register


def _google_status() -> dict[str, Any]:
    return {
        "secrets_dir": str(google_auth.SECRETS_DIR),
        "credentials_ok": google_auth.credentials_path().is_file(),
        "token_ok": google_auth.token_path().is_file(),
        "configured": google_auth.secrets_configured(),
    }


@register("mail", "status")
def mail_status(args: dict[str, Any]) -> dict[str, Any]:
    st = _google_status()
    return {
        "ok": True,
        "google": st,
        "status": "connected" if st["configured"] else "not_configured",
    }


@register("mail", "get_recent")
def mail_get_recent(args: dict[str, Any]) -> dict[str, Any]:
    if args.get("dry_run"):
        return {
            "ok": True,
            "dry_run": True,
            "threads": [],
            "count": 0,
            "source": "gmail-dry-run",
        }
    max_results = int(args.get("max") or args.get("max_results") or 20)
    only_unseen = bool(args.get("only_unseen") or args.get("unseen"))
    query = str(args.get("q") or args.get("query") or "")
    threads = gmail_client.list_messages(
        max_results=max_results,
        query=query,
        only_unseen=only_unseen,
        interactive=False,
    )
    return {
        "ok": True,
        "threads": threads,
        "count": len(threads),
        "source": "gmail",
    }


@register("mail", "get_by_id")
def mail_get_by_id(args: dict[str, Any]) -> dict[str, Any]:
    msg_id = args.get("id") or args.get("message_id")
    if not msg_id:
        return {"ok": False, "error": "missing_id", "message": "id oder message_id erforderlich"}
    message = gmail_client.get_message(str(msg_id), interactive=False)
    return {"ok": True, "message": message}


@register("mail", "parse_headers")
def mail_parse_headers(args: dict[str, Any]) -> dict[str, Any]:
    msg_id = args.get("id") or args.get("message_id")
    if not msg_id:
        return {"ok": False, "error": "missing_id", "message": "id oder message_id erforderlich"}
    headers = gmail_client.parse_headers_from_message(str(msg_id), interactive=False)
    return {"ok": True, "headers": headers}


def _mail_stub_actions(tenant_id: str) -> dict[str, Any]:
    """Synchroner Fallback wenn kein Google-Token — gleiche Daten wie mail_stub."""
    return {
        "status": "stub",
        "actions": [
            {
                "id": "mail-stub-1",
                "subject": "Hochschule — Kickoff Unterlagen",
                "action": "Antwort entwerfen / Termin bestätigen",
                "related_engagement": "eng-studenten-ss26",
            },
            {
                "id": "mail-stub-2",
                "subject": "SAP API Mgmt — Teilnehmerliste",
                "action": "Liste prüfen und Agenda anhängen",
                "related_engagement": "eng-sap-apim-kw-next",
            },
        ],
        "tenant_id": tenant_id,
    }


@register("mail", "list_open_actions")
def mail_list_open_actions(args: dict[str, Any]) -> dict[str, Any]:
    """Kompatibel mit daily_open_loops Stub-Interface."""
    tenant = str(args.get("tenant_id") or "nextchapter")
    if not google_auth.secrets_configured():
        stub = _mail_stub_actions(tenant)
        return {"ok": True, "status": stub["status"], "actions": stub["actions"]}

    result = mail_get_recent({**args, "only_unseen": True, "max": args.get("max") or 10})
    actions = []
    for t in result.get("threads") or []:
        actions.append({
            "id": t.get("id"),
            "subject": t.get("subject"),
            "from": t.get("from"),
            "snippet": t.get("snippet"),
        })
    return {"ok": True, "status": "connected", "actions": actions, "count": len(actions)}


@register("mail", "preview_invoices")
def mail_preview_invoices(args: dict[str, Any]) -> dict[str, Any]:
    if args.get("dry_run"):
        return {"ok": True, "dry_run": True, "count": 0, "invoices": []}
    from core.google.invoice.pipeline import preview_invoices

    tenant = str(args.get("tenant_id") or "nextchapter")
    return preview_invoices(tenant_id=tenant, interactive=False)


@register("mail", "run_invoices")
def mail_run_invoices(args: dict[str, Any]) -> dict[str, Any]:
    if args.get("dry_run") and not google_auth.secrets_configured():
        return {
            "ok": True,
            "dry_run": True,
            "status": "not_configured",
            "candidates": 0,
            "written": 0,
            "invoices": [],
            "message": "Google OAuth nicht konfiguriert",
        }
    if args.get("dry_run"):
        return {
            "ok": True,
            "dry_run": True,
            "candidates": 0,
            "written": 0,
            "invoices": [],
        }
    try:
        from core.google.invoice.pipeline import run_invoice_pipeline

        tenant = str(args.get("tenant_id") or "nextchapter")
        return run_invoice_pipeline(
            tenant_id=tenant,
            dry_run=bool(args.get("dry_run")),
            skip_archive=bool(args.get("skip_archive")),
            interactive=False,
        )
    except Exception as exc:
        if args.get("dry_run"):
            return {
                "ok": True,
                "dry_run": True,
                "candidates": 0,
                "written": 0,
                "invoices": [],
                "message": f"Dry-run fallback: {exc}",
            }
        raise


@register("mail", "export_steuer")
def mail_export_steuer(args: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from core.google.invoice.tax_export import DEFAULT_DEST, export_rechnungen

    year = int(args.get("year") or args.get("tax_year") or 2025)
    dest = Path(str(args.get("dest") or DEFAULT_DEST))
    dry_run = bool(args.get("dry_run"))
    stats = export_rechnungen(dest, tax_year=year, dry_run=dry_run)
    return {
        "ok": True,
        "dry_run": dry_run,
        "year": year,
        "dest": str(dest),
        **stats,
        "vendors": list(stats.get("vendors") or []),
        "files": list(stats.get("files") or []),
    }
