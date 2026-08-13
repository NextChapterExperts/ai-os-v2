"""Pytest Suite — Console Port 8090 Configuration Tests."""

import json
import os
from pathlib import Path

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PACKAGE_JSON = Path(REPO) / "core" / "console-web" / "package.json"


def test_package_json_uses_port_8090():
    """Prüft ob package.json in core/console-web auf Port 8090 konfiguriert ist."""
    assert PACKAGE_JSON.exists()
    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    assert "-p 8090" in scripts.get("dev", "")
    assert "-p 8090" in scripts.get("start", "")
