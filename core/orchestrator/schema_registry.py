"""Schema Registry — JSON Schema Export für die dynamische Console-UI."""

from __future__ import annotations

from typing import Any, Type
from sdk.dataproduct import DataProduct
from .dataproducts import DP_CLASS_BY_NODE_TYPE


def get_all_registered_schemas() -> dict[str, dict[str, Any]]:
    """Gibt die JSON-Schemata aller registrierten DataProducts zurück."""
    schemas: dict[str, dict[str, Any]] = {}
    for node_type, cls in DP_CLASS_BY_NODE_TYPE.items():
        if hasattr(cls, "model_json_schema"):
            schemas[node_type] = cls.model_json_schema()
    return schemas


def get_schema_by_node_type(node_type: str) -> dict[str, Any] | None:
    """Gibt das JSON-Schema für einen spezifischen node_type zurück."""
    cls = DP_CLASS_BY_NODE_TYPE.get(node_type)
    if cls and hasattr(cls, "model_json_schema"):
        return cls.model_json_schema()
    return None
