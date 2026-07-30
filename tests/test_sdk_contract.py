"""Pytest Suite — Agent SDK Contract Verification (P8)."""

import os
import sys
import pytest
from pydantic import Field, ValidationError

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from sdk.agent_base import AgentBase, ContractViolationError
from sdk.dataproduct import DataProduct
from sdk.tenant_context import TenantContext


class DummyInput(DataProduct):
    query: str = Field(min_length=1)


class DummyOutput(DataProduct):
    result_text: str
    storage_target: list[str] = ["G"]


class ValidDummyAgent(AgentBase[DummyInput, DummyOutput]):
    agent_id = "valid-dummy-agent"
    version = "1.0.0"
    input_schema = DummyInput
    output_schema = DummyOutput

    async def run(self, input_dp: DummyInput) -> DummyOutput:
        return DummyOutput(
            tenant_id=input_dp.tenant_id,
            produced_by=self.agent_id,
            result_text=f"Processed: {input_dp.query}",
        )


def test_agent_contract_validation_missing_fields():
    """Agent ohne agent_id oder Schemata wirft ContractViolationError."""
    with pytest.raises(ContractViolationError, match="agent_id ist Pflichtfeld"):
        class InvalidAgent1(AgentBase):
            agent_id = ""
            version = "1.0.0"
            input_schema = DummyInput
            output_schema = DummyOutput
            async def run(self, input_dp): pass
        InvalidAgent1()

    with pytest.raises(ContractViolationError, match="input_schema ist Pflichtfeld"):
        class InvalidAgent2(AgentBase):
            agent_id = "test"
            version = "1.0.0"
            input_schema = None
            output_schema = DummyOutput
            async def run(self, input_dp): pass
        InvalidAgent2()


def test_dataproduct_tenant_id_validation():
    """DataProduct wirft ValidationError bei leerer tenant_id."""
    with pytest.raises(ValidationError):
        DummyInput(query="test", tenant_id="")


@pytest.mark.asyncio
async def test_agent_execute_success():
    """AgentBase.execute() führt den Run durch und liefert ein valides DataProduct."""
    agent = ValidDummyAgent()
    input_data = {"query": "Hallo Welt", "tenant_id": "nextchapter"}
    output = await agent.execute(input_data)

    assert isinstance(output, DummyOutput)
    assert output.result_text == "Processed: Hallo Welt"
    assert output.produced_by == "valid-dummy-agent"
    assert output.tenant_id == "nextchapter"


@pytest.mark.asyncio
async def test_agent_execute_invalid_input():
    """Ungültiger Input wirft ContractViolationError."""
    agent = ValidDummyAgent()
    with pytest.raises(ContractViolationError):
        await agent.execute({"query": ""})  # query min_length=1 verletzung
