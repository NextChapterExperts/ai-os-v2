"""Pytest Suite — Role-Based Auth & Login Tests."""

import os
from pathlib import Path

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONSOLE_WEB_DIR = Path(REPO) / "core" / "console-web"


def test_auth_module_exists():
    """Prüft ob lib/auth.ts existiert und die Zugangsdaten für peter und admin enthält."""
    auth_ts = CONSOLE_WEB_DIR / "src" / "lib" / "auth.ts"
    assert auth_ts.exists()
    content = auth_ts.read_text(encoding="utf-8")
    assert "VALID_CREDENTIALS" in content
    assert "peter" in content
    assert "admin" in content
    assert "user" in content


def test_login_page_exists():
    """Prüft ob die Login-Seite src/app/login/page.tsx existiert."""
    login_page = CONSOLE_WEB_DIR / "src" / "app" / "login" / "page.tsx"
    assert login_page.exists()
    content = login_page.read_text(encoding="utf-8")
    assert '"use client"' in content
    assert "peter" in content
    assert "admin" in content
    assert "loginUser" in content
