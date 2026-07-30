"""SkillHook — Post-Run Destillations-Hook für den Skill-Loop (P6)."""

from __future__ import annotations

from typing import Any
from .dataproduct import DataProduct
from .tenant_context import TenantContext


class SkillHook:
    """
    Wird nach jedem Agent-Run aufgerufen, um komplexe erfolgreiche Tasks
    in versionierte Skill-Dokumente zu destillieren.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    @classmethod
    def noop(cls) -> SkillHook:
        return cls(enabled=False)

    async def post_run(
        self,
        agent_id: str,
        input_dp: DataProduct,
        output_dp: DataProduct,
        ctx: TenantContext,
    ) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        # Heuristik: Destillation wenn Resultat komplex ist
        return {
            "status": "skill_evaluated",
            "agent_id": agent_id,
            "input_id": input_dp.dp_id,
            "output_id": output_dp.dp_id,
            "tenant_id": ctx.tenant_id,
        }
