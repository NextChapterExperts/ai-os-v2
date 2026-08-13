"""Unit-Tests für den nativen MCP web_search Adapter."""

from core.mcp_gateway.adapters.registry import allowlist, dispatch
from core.mcp_gateway.adapters.web_search import execute_web_search


def test_web_search_registered_in_mcp_registry():
    """Prüfe ob web_search.search in der MCP Registry gelistet ist."""
    registered = allowlist()
    assert "web_search" in registered
    assert "search" in registered["web_search"]


def test_web_search_dispatch_returns_valid_structure():
    """Testet den Aufruf des web_search Adapters über die Registry."""
    res = dispatch("web_search", "search", {"q": "Docker AI MCP", "num": 3})
    assert res["ok"] is True
    assert "results" in res
    assert isinstance(res["results"], list)


def test_web_search_empty_query_returns_empty_list():
    """Prüfe leere Suchanfrage."""
    res = execute_web_search({"q": ""})
    assert res["ok"] is True
    assert res["results"] == []
