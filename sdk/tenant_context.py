"""TenantContext — Laufzeit-Kontext für AI-OS v2 Agenten."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TenantContext:
    """
    Trägt alle plattformweiten Informationen und injected Clients für einen Agenten.
    """
    tenant_id: str = "nextchapter"
    compute_mode: Literal["sovereign", "balanced", "premium"] = "sovereign"
    active_packages: list[str] = field(default_factory=lambda: ["platform-core"])

    # Injected Services
    llm: Any = None
    dp_client: Any = None
    skill_store: Any = None

    @classmethod
    def for_tenant(cls, tenant_id: str = "nextchapter", compute_mode: str = "sovereign") -> TenantContext:
        """Erstellt einen TenantContext für Tests oder Ausführung."""
        return cls(
            tenant_id=tenant_id,
            compute_mode=compute_mode, # type: ignore
        )
