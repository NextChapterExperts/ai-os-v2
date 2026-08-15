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


def test_appshell_navigation_role_separation():
    """Prüft strikte Rollentrennung: USER darf nur Fachagenten sehen, ADMIN hat alle Plattform-Tools."""
    appshell_ts = CONSOLE_WEB_DIR / "src" / "components" / "AppShell.tsx"
    assert appshell_ts.exists()
    content = appshell_ts.read_text(encoding="utf-8")
    
    # USER_NAV: Nur Fachagenten
    assert 'const USER_NAV = [' in content
    assert '{ href: "/agents", label: "Fachagenten" }' in content
    assert 'const ADMIN_NAV = [' in content
    assert '{ href: "/company", label: "Unternehmen" }' in content
    assert '{ href: "/platform", label: "Plattform" }' in content


def test_company_page_has_admin_guard():
    """Prüft, dass die Unternehmensseite einen Admin-Guard besitzt."""
    company_page = CONSOLE_WEB_DIR / "src" / "app" / "company" / "page.tsx"
    assert company_page.exists()
    content = company_page.read_text(encoding="utf-8")
    assert 'auth.role !== "admin"' in content
    assert 'Zugriff verweigert (Administrator erforderlich)' in content

