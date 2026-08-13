"""Docker MCP Catalog & Gateway Adapter (Option 1 - P5).

Ermöglicht den Aufruf von containerisierten MCP-Servern aus dem Docker Catalog/Hub (docker-mcp)
unter Beibehaltung der VIRKI Governance, Rate-Caps und Hash-Auditierung.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

from core.mcp_gateway.adapters.registry import register


class DockerMCPAdapter:
    """Treiber für containerisierte MCP-Server via Docker / docker-mcp CLI."""

    def __init__(self, catalog_server: str):
        self.catalog_server = catalog_server

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tenant_id = arguments.get("tenant_id", "nextchapter")

        # Prüfe ob Docker-Daemon / docker-mcp verfügbar ist
        docker_bin = shutil.which("docker")
        if not docker_bin and not os.environ.get("MOCK_DOCKER_MCP"):
            return {
                "ok": True,
                "server": self.catalog_server,
                "tool": tool_name,
                "execution_mode": "emulator",
                "result": {
                    "status": "simulated",
                    "catalog_server": self.catalog_server,
                    "tool": tool_name,
                    "arguments": arguments,
                    "output": f"Simulierter MCP Catalog Aufruf für {self.catalog_server}.{tool_name}",
                },
                "tenant_id": tenant_id,
            }

        # Ausführung über Subprocess (Real oder Mock-Umgebung)
        if os.environ.get("MOCK_DOCKER_MCP"):
            return {
                "ok": True,
                "server": self.catalog_server,
                "tool": tool_name,
                "execution_mode": "mock",
                "result": {
                    "status": "success",
                    "catalog_server": self.catalog_server,
                    "tool": tool_name,
                    "data": {"query_result": "mock_data", "args": arguments},
                },
                "tenant_id": tenant_id,
            }

        try:
            # docker-mcp CLI Aufruf
            cmd = [
                docker_bin,
                "mcp",
                "exec",
                self.catalog_server,
                tool_name,
                "--args",
                json.dumps(arguments),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                try:
                    payload = json.loads(res.stdout)
                except Exception:
                    payload = {"raw_output": res.stdout.strip()}
                return {
                    "ok": True,
                    "server": self.catalog_server,
                    "tool": tool_name,
                    "execution_mode": "docker_container",
                    "result": payload,
                    "tenant_id": tenant_id,
                }
            else:
                return {
                    "ok": False,
                    "server": self.catalog_server,
                    "tool": tool_name,
                    "error": "docker_mcp_failed",
                    "message": res.stderr.strip() or f"Returncode {res.returncode}",
                }
        except Exception as exc:
            return {
                "ok": False,
                "server": self.catalog_server,
                "tool": tool_name,
                "error": "docker_exec_exception",
                "message": str(exc),
            }


# Registrierung vordefinierter Docker MCP Catalog Server
DOCKER_CATALOG_SERVERS = {
    "docker_postgres": ["query", "list_tables", "describe_table"],
    "docker_github": ["create_issue", "list_pull_requests", "get_file_content"],
    "docker_slack": ["send_message", "list_channels"],
    "docker_brave_search": ["web_search", "local_search"],
}

for _server_id, _tools in DOCKER_CATALOG_SERVERS.items():
    _adapter = DockerMCPAdapter(_server_id)
    for _tname in _tools:

        def _make_handler(srv: str, tname: str, adapter: DockerMCPAdapter):
            def handler(args: dict[str, Any]) -> dict[str, Any]:
                return adapter.execute_tool(tname, args)

            return handler

        register(_server_id, _tname)(_make_handler(_server_id, _tname, _adapter))
