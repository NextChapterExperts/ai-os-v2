"""Pytest Suite — DataProduct Schema Export API Tests."""

import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from core.orchestrator.schema_registry import get_all_registered_schemas, get_schema_by_node_type


def test_get_all_registered_schemas():
    """Prüft ob registrierte DataProduct-Klassen gültige JSON-Schemata liefern."""
    schemas = get_all_registered_schemas()
    assert len(schemas) > 0
    assert "org:Offering" in schemas
    assert "properties" in schemas["org:Offering"]
    assert "name" in schemas["org:Offering"]["properties"]


def test_get_schema_by_node_type():
    """Prüft gezielten Abruf eines Schemas für ein spezifisches DataProduct."""
    schema = get_schema_by_node_type("org:Offering")
    assert schema is not None
    assert schema.get("title") == "OrgOffering"
    assert "name" in schema.get("properties", {})

    invalid_schema = get_schema_by_node_type("nonexistent:Type")
    assert invalid_schema is None
