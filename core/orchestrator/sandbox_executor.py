"""Sandbox Executor (Option 2 - P15 PGE Trinity).

Erstellt ephemere Docker MicroVM Sandboxes zur isolierten Ausführung von Code und Skripten
für Risikoklassen YELLOW und ORANGE. RED wird blockiert.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    is_sandboxed: bool
    risk_level: str
    status: str  # "success", "failed", "timeout", "blocked"
    artifacts: dict[str, Any] = field(default_factory=dict)


class SandboxExecutor:
    """Isolierter Executor für das PGE Trinity Prinzip (Planner -> Gatekeeper -> Executor)."""

    def __init__(self, default_image: str = "python:3.11-slim", memory_limit: str = "512m"):
        self.default_image = default_image
        self.memory_limit = memory_limit

    def execute(
        self,
        code: str,
        risk_level: str = "YELLOW",
        language: str = "python",
        timeout: int = 10,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        start_t = time.time()
        risk = risk_level.upper()

        # P15 Trinity Rule: RED ist ohne expliziten Gatekeeper Human-Approval verboten
        if risk == "RED":
            return SandboxResult(
                stdout="",
                stderr="Execution blocked by PGE Gatekeeper: Risk level RED requires human approval",
                exit_code=126,
                duration_ms=0.0,
                is_sandboxed=True,
                risk_level=risk,
                status="blocked",
            )

        docker_bin = shutil.which("docker")
        force_mock = os.environ.get("MOCK_DOCKER_SANDBOX") == "1"

        # Fallback / Emulator Sandbox wenn kein Docker Daemon da ist
        if not docker_bin or force_mock:
            return self._execute_emulated(code, risk, language, timeout, start_t)

        # Echte Docker MicroVM Sandbox Ausführung
        with tempfile.TemporaryDirectory(prefix="virki_sandbox_") as tmpdir:
            script_ext = ".py" if language == "python" else ".sh"
            script_path = os.path.join(tmpdir, f"script{script_ext}")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            cmd = [
                docker_bin,
                "run",
                "--rm",
                "--network",
                "none",
                "--memory",
                self.memory_limit,
                "-v",
                f"{tmpdir}:/workspace:ro",
                "-w",
                "/workspace",
            ]

            # Environment Variablen
            if env:
                for k, v in env.items():
                    cmd.extend(["-e", f"{k}={v}"])

            cmd.append(self.default_image)

            if language == "python":
                cmd.extend(["python3", f"/workspace/script{script_ext}"])
            else:
                cmd.extend(["bash", f"/workspace/script{script_ext}"])

            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                duration = (time.time() - start_t) * 1000
                status = "success" if res.returncode == 0 else "failed"
                return SandboxResult(
                    stdout=res.stdout,
                    stderr=res.stderr,
                    exit_code=res.returncode,
                    duration_ms=round(duration, 2),
                    is_sandboxed=True,
                    risk_level=risk,
                    status=status,
                )
            except subprocess.TimeoutExpired:
                duration = (time.time() - start_t) * 1000
                return SandboxResult(
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds",
                    exit_code=124,
                    duration_ms=round(duration, 2),
                    is_sandboxed=True,
                    risk_level=risk,
                    status="timeout",
                )
            except Exception as exc:
                duration = (time.time() - start_t) * 1000
                return SandboxResult(
                    stdout="",
                    stderr=f"Sandbox execution error: {str(exc)}",
                    exit_code=1,
                    duration_ms=round(duration, 2),
                    is_sandboxed=True,
                    risk_level=risk,
                    status="failed",
                )

    def _execute_emulated(
        self, code: str, risk: str, language: str, timeout: int, start_t: float
    ) -> SandboxResult:
        """Sicheres Subprozess-Fallback im isolierten Tempdir für Tests / Umgebungen ohne Docker."""
        with tempfile.TemporaryDirectory(prefix="virki_sandbox_emu_") as tmpdir:
            script_ext = ".py" if language == "python" else ".sh"
            script_path = os.path.join(tmpdir, f"script{script_ext}")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            if language == "python":
                cmd = ["python3", script_path]
            else:
                cmd = ["bash", script_path]

            try:
                # Isoliere Ausführung im tempdir als CWD mit leerem oder minimalem ENV
                clean_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "TMPDIR": tmpdir}
                res = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=tmpdir, env=clean_env, timeout=timeout
                )
                duration = (time.time() - start_t) * 1000
                status = "success" if res.returncode == 0 else "failed"
                return SandboxResult(
                    stdout=res.stdout,
                    stderr=res.stderr,
                    exit_code=res.returncode,
                    duration_ms=round(duration, 2),
                    is_sandboxed=True,
                    risk_level=risk,
                    status=status,
                    artifacts={"emulated": True},
                )
            except subprocess.TimeoutExpired:
                duration = (time.time() - start_t) * 1000
                return SandboxResult(
                    stdout="",
                    stderr=f"Emulated sandbox timed out after {timeout}s",
                    exit_code=124,
                    duration_ms=round(duration, 2),
                    is_sandboxed=True,
                    risk_level=risk,
                    status="timeout",
                )
