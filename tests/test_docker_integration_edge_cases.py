"""Erweiterte Edge-Case & Isolations-Tests für Docker MCP & Sandbox Integrationen."""

import os
from unittest.mock import patch
import pytest

from core.mcp_gateway.adapters.docker_adapter import DockerMCPAdapter
from core.orchestrator.sandbox_executor import SandboxExecutor


def test_docker_adapter_subprocess_exception_handling():
    """Prüfe Fehlerbehandlung wenn Subprocess im Docker MCP Adapter fehlschlägt."""
    with patch("shutil.which", return_value="/usr/bin/docker"):
        with patch("subprocess.run", side_effect=RuntimeError("Subprocess launch error")):
            adapter = DockerMCPAdapter("docker_postgres")
            res = adapter.execute_tool("query", {"sql": "SELECT 1"})
            assert res["ok"] is False
            assert res["error"] == "docker_exec_exception"
            assert "Subprocess launch error" in res["message"]


def test_docker_adapter_subprocess_return_code_error():
    """Prüfe Behandlung von Nicht-Null Return-Codes des Docker CLI."""
    class MockProcess:
        returncode = 1
        stdout = ""
        stderr = "Docker daemon connection refused"

    with patch("shutil.which", return_value="/usr/bin/docker"):
        with patch("subprocess.run", return_value=MockProcess()):
            adapter = DockerMCPAdapter("docker_github")
            res = adapter.execute_tool("list_pull_requests", {})
            assert res["ok"] is False
            assert res["error"] == "docker_mcp_failed"
            assert "connection refused" in res["message"]


def test_sandbox_executor_bash_script_execution():
    """Testet die Ausführung von Bash-Skripten in der Sandbox."""
    executor = SandboxExecutor()
    code = "echo 'Bash Sandbox Test' && exit 0"
    res = executor.execute(code, risk_level="YELLOW", language="bash")
    assert res.status == "success"
    assert "Bash Sandbox Test" in res.stdout


def test_sandbox_executor_custom_env_passing():
    """Testet die Weitergabe von benutzerdefinierten Umgebungsvariablen in der Sandbox."""
    executor = SandboxExecutor()
    code = "import os; print(os.environ.get('VIRKI_TEST_VAR', 'NONE'))"
    res = executor.execute(code, risk_level="YELLOW", language="python", env={"VIRKI_TEST_VAR": "SUPER_SECRET_TOKEN"})
    assert res.status == "success"
    assert "SUPER_SECRET_TOKEN" in res.stdout
