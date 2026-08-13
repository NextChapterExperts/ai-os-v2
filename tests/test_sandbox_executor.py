"""Unit & Integration Tests für PGE Trinity Sandbox Executor (Option 2 - P15)."""

import os
import pytest

from core.orchestrator.sandbox_executor import SandboxExecutor, SandboxResult


def test_sandbox_successful_python_execution():
    """Testet erfolgreiche Ausführung eines Python-Skripts in der Sandbox."""
    executor = SandboxExecutor()
    code = "print('Hello from Virki Sandbox')"
    res = executor.execute(code, risk_level="YELLOW", language="python")

    assert isinstance(res, SandboxResult)
    assert res.status == "success"
    assert res.exit_code == 0
    assert "Hello from Virki Sandbox" in res.stdout
    assert res.is_sandboxed is True
    assert res.risk_level == "YELLOW"
    assert res.duration_ms >= 0.0


def test_sandbox_red_risk_blocked():
    """Prüfe ob Risikoklasse RED gemäß PGE Trinity (P15) blockiert wird."""
    executor = SandboxExecutor()
    code = "import os; os.system('rm -rf /')"
    res = executor.execute(code, risk_level="RED", language="python")

    assert res.status == "blocked"
    assert res.exit_code == 126
    assert "blocked by PGE Gatekeeper" in res.stderr
    assert res.risk_level == "RED"


def test_sandbox_script_error_captured():
    """Prüfe ob Fehler im Skript korrekt erfasst werden."""
    executor = SandboxExecutor()
    code = "raise ValueError('Custom Sandbox Error')"
    res = executor.execute(code, risk_level="ORANGE", language="python")

    assert res.status == "failed"
    assert res.exit_code != 0
    assert "ValueError: Custom Sandbox Error" in res.stderr


def test_sandbox_timeout_enforcement():
    """Prüfe ob Timeouts erzwungen werden."""
    executor = SandboxExecutor()
    code = "import time; time.sleep(10)"
    res = executor.execute(code, risk_level="YELLOW", language="python", timeout=1)

    assert res.status == "timeout"
    assert res.exit_code == 124
    assert "timed out" in res.stderr


def test_sandbox_environment_emulation_forced():
    """Testet erzwungene Emulations-Sandbox via MOCK_DOCKER_SANDBOX=1."""
    os.environ["MOCK_DOCKER_SANDBOX"] = "1"
    try:
        executor = SandboxExecutor()
        code = "import sys; print(f'Python version: {sys.version_info.major}')"
        res = executor.execute(code, risk_level="GREEN", language="python")

        assert res.status == "success"
        assert "Python version: 3" in res.stdout
        assert res.artifacts.get("emulated") is True
    finally:
        del os.environ["MOCK_DOCKER_SANDBOX"]
