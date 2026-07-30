"""AgentBase — Der verbindliche Contract für jeden AI-OS v2 Agenten (P8)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import ValidationError

from .dataproduct import DataProduct
from .mcp_adapter import MCPAdapter
from .skill_hook import SkillHook
from .tenant_context import TenantContext

InputDP = TypeVar("InputDP", bound=DataProduct)
OutputDP = TypeVar("OutputDP", bound=DataProduct)


class ContractViolationError(ValueError):
    """Wird geworfen, wenn ein Agent die SDK-Vorgaben nicht einhält."""
    pass


class AgentBase(ABC, Generic[InputDP, OutputDP]):
    """
    Basisklasse für alle AI-OS v2-Agenten.

    Pflichtfelder:
        agent_id:      str      — z.B. "research-agent"
        version:       str      — z.B. "1.0.0"
        input_schema:  type     — Pydantic-Klasse(DataProduct)
        output_schema: type     — Pydantic-Klasse(DataProduct)
    """

    agent_id: ClassVar[str]
    version: ClassVar[str]
    input_schema: ClassVar[type[DataProduct]]
    output_schema: ClassVar[type[DataProduct]]

    def __init__(
        self,
        ctx: TenantContext | None = None,
        mcp: MCPAdapter | None = None,
        skill_hook: SkillHook | None = None,
    ):
        self._validate_contract()
        self.ctx = ctx or TenantContext.for_tenant()
        self.mcp = mcp or MCPAdapter(tenant_id=self.ctx.tenant_id, agent_id=self.agent_id)
        self.skill_hook = skill_hook or SkillHook.noop()

    def _validate_contract(self) -> None:
        """Prüft zur Laufzeit bei Instanziierung den Agent-Contract (P8)."""
        if not hasattr(self, "agent_id") or not getattr(self, "agent_id"):
            raise ContractViolationError(f"{self.__class__.__name__}: agent_id ist Pflichtfeld")
        if not hasattr(self, "version") or not getattr(self, "version"):
            raise ContractViolationError(f"{self.__class__.__name__}: version ist Pflichtfeld")
        if not hasattr(self, "input_schema") or getattr(self, "input_schema") is None:
            raise ContractViolationError(f"{self.__class__.__name__}: input_schema ist Pflichtfeld")
        if not hasattr(self, "output_schema") or getattr(self, "output_schema") is None:
            raise ContractViolationError(f"{self.__class__.__name__}: output_schema ist Pflichtfeld")

    @abstractmethod
    async def run(self, input_dp: InputDP) -> OutputDP:
        """
        Kernlogik des Agenten.
        Muss von der Subklasse implementiert werden.
        """
        ...

    async def execute(self, input_dp: InputDP | dict[str, Any]) -> OutputDP:
        """
        Framework-Wrapper.
        Validiert Input, führt run() aus, validiert Output, committet DataProduct und triggert Skill-Hook.
        """
        # 1. Input validieren
        if isinstance(input_dp, dict):
            try:
                validated_input = self.input_schema.model_validate(input_dp)
            except ValidationError as exc:
                raise ContractViolationError(f"Input ungültig für {self.agent_id}: {exc}") from exc
        else:
            validated_input = input_dp

        # 2. Kernlogik ausführen
        raw_output = await self.run(validated_input)

        # 3. Output validieren
        if isinstance(raw_output, dict):
            try:
                validated_output = self.output_schema.model_validate(raw_output)
            except ValidationError as exc:
                raise ContractViolationError(f"Output ungültig für {self.agent_id}: {exc}") from exc
        else:
            validated_output = raw_output

        # 4. DP-Commit erzwingen (falls DP-Client injected oder Orchestrator verfügbar)
        if self.ctx.dp_client and hasattr(self.ctx.dp_client, "commit"):
            await self.ctx.dp_client.commit(validated_output)

        # 5. Post-Run Skill-Hook
        await self.skill_hook.post_run(
            agent_id=self.agent_id,
            input_dp=validated_input,
            output_dp=validated_output,
            ctx=self.ctx,
        )

        return validated_output # type: ignore
