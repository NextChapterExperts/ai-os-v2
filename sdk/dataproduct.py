"""DataProduct Base Class (P8 Agent-Contract & Schema Registry)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar

from pydantic import BaseModel, Field, field_validator


class DataProduct(BaseModel):
    """
    Basisklasse für alle AI-OS v2 Datenprodukte.
    Jeder Agent-Input und -Output MUSS von dieser Klasse erben.
    """
    dp_id: str = Field(default_factory=lambda: f"dp-{uuid.uuid4().hex[:12]}")
    schema_version: str = "1.0"
    tenant_id: str = Field(default="nextchapter", min_length=1)
    produced_by: str = Field(default="system")
    produced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workflow_run_id: str | None = None

    # Speicher-Steuerung
    storage_target: list[str] = Field(default_factory=lambda: ["G"])
    ingest_recommended: bool = False

    @field_validator("tenant_id")

    @classmethod
    def validate_tenant_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("tenant_id darf nicht leer sein")
        return v.strip()

    @classmethod
    def get_ui_schema(cls) -> dict[str, Any]:
        """JSON-Schema für die Console-UI — ohne interne DataProduct-Felder."""
        internal = {
            "dp_id",
            "schema_version",
            "tenant_id",
            "produced_by",
            "produced_at",
            "workflow_run_id",
            "storage_target",
            "ingest_recommended",
        }
        schema = cls.model_json_schema()
        props = schema.get("properties") or {}
        schema["properties"] = {k: v for k, v in props.items() if k not in internal}
        if schema.get("required"):
            schema["required"] = [r for r in schema["required"] if r not in internal]
        return schema
