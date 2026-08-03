"""Google OAuth + API-Hilfsmodule für AI-OS V2 (Plattform-Kern)."""

from .scopes import GOOGLE_SCOPES, ensure_scopes, tool_required_scopes

__all__ = ["GOOGLE_SCOPES", "ensure_scopes", "tool_required_scopes"]
