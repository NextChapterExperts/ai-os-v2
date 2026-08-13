"""Pytest Suite — Prototype Route & Radial Navigation Tests."""

import os
from pathlib import Path

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONSOLE_WEB_DIR = Path(REPO) / "core" / "console-web"


def test_prototype_page_exists():
    """Prüft ob die isolierte Prototyp-Seite src/app/prototype/page.tsx existiert."""
    prototype_page = CONSOLE_WEB_DIR / "src" / "app" / "prototype" / "page.tsx"
    assert prototype_page.exists()
    content = prototype_page.read_text(encoding="utf-8")
    assert '"use client"' in content
    assert "RadialNavigationWheel" in content
    assert "detectSuggestedAgent" in content
    assert "SEARCH AGENT" in content
    assert "qwen2.5-coder:14b" in content


def test_radial_navigation_wheel_component_exists():
    """Prüft ob die RadialNavigationWheel Komponente existiert und alle 5 Fachagenten enthält."""
    component = CONSOLE_WEB_DIR / "src" / "components" / "RadialNavigationWheel.tsx"
    assert component.exists()
    content = component.read_text(encoding="utf-8")
    assert '"use client"' in content
    assert "RADIAL_AGENTS" in content
    assert "handwerker" in content
    assert "blog" in content
    assert "meetings" in content
    assert "email" in content
    assert "research" in content
