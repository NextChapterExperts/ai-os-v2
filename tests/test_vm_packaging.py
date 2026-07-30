"""Pytest Suite — Appliance VM Packaging & Onboarding Tests."""

import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

APPLIANCE_DIR = Path(REPO) / "appliance"


def test_cloud_init_file_exists():
    """Prüft ob die cloud-init Konfigurationsdatei vorhanden ist."""
    cloud_init = APPLIANCE_DIR / "cloud-init.yaml"
    assert cloud_init.exists()
    content = cloud_init.read_text(encoding="utf-8")
    assert "#cloud-config" in content
    assert "aios-orchestrator.service" in content
    assert "aios-mcp-gateway.service" in content


def test_image_build_script_dry_run():
    """Prüft die Ausführung des Image-Build-Skripts im Dry-Run Modus."""
    script = APPLIANCE_DIR / "image-build.sh"
    assert script.exists()

    res = subprocess.run(
        [str(script), "--dry-run"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "DRY-RUN abgeschlossen" in res.stdout


def test_init_tenant_vm_script_help():
    """Prüft die Ausführung des Mandanten-VM Onboarding Skripts bei fehlendem Parameter."""
    script = APPLIANCE_DIR / "init-tenant-vm.sh"
    assert script.exists()

    res = subprocess.run(
        [str(script)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "Fehler: Parameter --tenant" in res.stdout
