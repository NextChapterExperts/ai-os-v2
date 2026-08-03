"""Google OAuth — zentrale Pfade für AI-OS V2.

Secrets liegen in secrets/google/ (nicht committen) oder unter GOOGLE_TOOLS_SECRETS.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from .scopes import ScopeError, ensure_scopes

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SECRETS = _REPO_ROOT / "secrets" / "google"

SECRETS_DIR = Path(
    os.getenv("GOOGLE_TOOLS_SECRETS", str(_DEFAULT_SECRETS))
).expanduser()


def credentials_path() -> Path:
    return SECRETS_DIR / "credentials.json"


def token_path(name: str = "token.json") -> Path:
    return SECRETS_DIR / name


def secrets_configured() -> bool:
    return credentials_path().is_file() and token_path().is_file()


def load_credentials(
    scopes: list[str],
    token_name: str = "token.json",
    *,
    interactive: bool = True,
    tool: str | None = None,
) -> Credentials:
    """Lädt oder erneuert OAuth-Credentials für die angegebenen Scopes."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    cred_path = credentials_path()
    tok_path = token_path(token_name)
    requested = set(scopes)
    tool_label = tool or "google-api"

    if not cred_path.is_file():
        raise FileNotFoundError(
            f"credentials.json nicht gefunden: {cred_path}\n"
            "OAuth-Client-JSON aus Google Cloud Console nach secrets/google/ legen."
        )

    existing_scopes: set[str] = set()
    if tok_path.is_file():
        try:
            existing = json.loads(tok_path.read_text(encoding="utf-8"))
            existing_scopes = set(existing.get("scopes") or [])
        except (OSError, json.JSONDecodeError):
            existing_scopes = set()

    creds: Credentials | None = None
    if tok_path.is_file():
        try:
            # Volle Token-Scopes laden — kein Subset, sonst schlägt Refresh mit invalid_scope fehl
            creds = Credentials.from_authorized_user_file(str(tok_path))
        except Exception:
            creds = None

    if creds and creds.valid:
        granted = set(creds.scopes or existing_scopes or [])
        try:
            ensure_scopes(granted, requested, tool=tool_label, token_path=str(tok_path))
        except ScopeError:
            if not interactive:
                raise
            creds = None
        else:
            return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            try:
                tok_path.parent.mkdir(parents=True, exist_ok=True)
                tok_path.write_text(creds.to_json(), encoding="utf-8")
            except OSError:
                pass
            granted = set(creds.scopes or existing_scopes or [])
            ensure_scopes(granted, requested, tool=tool_label, token_path=str(tok_path))
            return creds
        except ScopeError:
            if not interactive:
                raise
            creds = None
        except Exception as exc:
            if not interactive:
                raise RuntimeError(
                    f"Token konnte nicht erneuert werden ({tok_path}): {exc}. "
                    "Lokal erneuern: python scripts/test_google_connection.py"
                ) from exc
            creds = None

    if not interactive:
        raise RuntimeError(f"Token ungültig, abgelaufen oder Scope unvollständig: {tok_path}")

    flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), scopes)
    creds = flow.run_local_server(port=0)
    tok_path.parent.mkdir(parents=True, exist_ok=True)
    tok_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def load_for_tool(
    server: str,
    tool: str,
    *,
    token_name: str = "token.json",
    interactive: bool = False,
) -> Credentials:
    """Lädt Credentials mit Scope-Validierung für ein MCP-Tool."""
    from google.oauth2.credentials import Credentials

    from .scopes import tool_required_scopes

    required = tool_required_scopes(server, tool)
    if not required:
        return load_credentials([], token_name, interactive=interactive, tool=f"{server}.{tool}")
    return load_credentials(
        required,
        token_name,
        interactive=interactive,
        tool=f"{server}.{tool}",
    )
