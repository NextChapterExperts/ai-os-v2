"""Unit & Integration Tests für Docker MCP Catalog & Gateway Integration (Option 1 - P5)."""

import os
from unittest.mock import patch
import pytest

from core.mcp_gateway.adapters.docker_adapter import DOCKER_CATALOG_SERVERS, DockerMCPAdapter
from core.mcp_gateway.adapters.registry import allowlist, dispatch


def test_docker_catalog_servers_registered():
    """Prüfe ob alle definierten Docker Catalog Server in der MCP Registry gelistet sind."""
    registered = allowlist()
    for server_id, expected_tools in DOCKER_CATALOG_SERVERS.items():
        assert server_id in registered, f"Server {server_id} fehlt in Registry"
        for tool in expected_tools:
            assert tool in registered[server_id], f"Tool {tool} fehlt in {server_id}"


def test_docker_mcp_dispatch_mock():
    """Testet den MCP Tool Dispatch über den Docker Adapter im Mock-Modus."""
    os.environ["MOCK_DOCKER_MCP"] = "1"
    try:
        res = dispatch("docker_postgres", "query", {"sql": "SELECT 1;", "tenant_id": "nextchapter"})
        assert res["ok"] is True
        assert res["server"] == "docker_postgres"
        assert res["tool"] == "query"
        assert res["result"]["status"] == "success"
    finally:
        del os.environ["MOCK_DOCKER_MCP"]


def test_docker_mcp_dispatch_emulated_without_mock_env():
    """Testet Fallback/Emulation wenn MOCK_DOCKER_MCP nicht gesetzt ist und docker binary nicht vorhanden oder gemockt wird."""
    with patch("shutil.which", return_value=None):
        adapter = DockerMCPAdapter("docker_github")
        res = adapter.execute_tool("create_issue", {"title": "Test Issue", "tenant_id": "nextchapter"})
        assert res["ok"] is True
        assert res["execution_mode"] == "emulator"
        assert res["result"]["status"] == "simulated"


def test_docker_mcp_invalid_tool():
    """Prüfe Fehlerbehandlung bei nicht registrierten Tools."""
    res = dispatch("docker_postgres", "non_existing_tool", {})
    assert res["ok"] is False
    assert res["error"] == "unknown_tool"


def test_docker_mcp_all_catalog_servers_dispatchable():
    """Testet den Aufruf jedes Catalog Tools im Mock-Modus."""
    os.environ["MOCK_DOCKER_MCP"] = "1"
    try:
        for server_id, tools in DOCKER_CATALOG_SERVERS.items():
            for tool_name in tools:
                res = dispatch(server_id, tool_name, {"tenant_id": "nextchapter"})
                assert res["ok"] is True, f"Dispatch fehlgeschlagen für {server_id}.{tool_name}"
    finally:
        del os.environ["MOCK_DOCKER_MCP"]
