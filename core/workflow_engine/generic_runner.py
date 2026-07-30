"""Generic Workflow Runner (P4/P7/P8)."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Type

from sdk.dataproduct import DataProduct
from sdk.agent_base import AgentBase
from core.orchestrator.dp_service import commit_dataproduct


class RegisteredWorkflow:
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str,
        input_schema: Type[DataProduct],
        output_schema: Type[DataProduct],
        handler: Callable[[Any], Any],
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.handler = handler


_WORKFLOW_REGISTRY: dict[str, RegisteredWorkflow] = {}


def register_workflow(
    workflow_id: str,
    name: str,
    description: str,
    input_schema: Type[DataProduct],
    output_schema: Type[DataProduct],
    handler: Callable[[Any], Any],
) -> RegisteredWorkflow:
    wf = RegisteredWorkflow(workflow_id, name, description, input_schema, output_schema, handler)
    _WORKFLOW_REGISTRY[workflow_id] = wf
    return wf


def get_workflow_registry() -> dict[str, RegisteredWorkflow]:
    return _WORKFLOW_REGISTRY


async def execute_registered_workflow(
    workflow_id: str,
    tenant_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    wf = _WORKFLOW_REGISTRY.get(workflow_id)
    if not wf:
        raise ValueError(f"Workflow '{workflow_id}' ist nicht registriert.")

    run_id = f"wf-run-{uuid.uuid4().hex[:8]}"
    validated_input = wf.input_schema.model_validate({**payload, "tenant_id": tenant_id, "workflow_run_id": run_id})

    # Ausführung des deterministischen Handlers
    res = wf.handler(validated_input)
    if hasattr(res, "__await__"):
        res = await res

    if isinstance(res, dict):
        validated_output = wf.output_schema.model_validate({**res, "tenant_id": tenant_id, "workflow_run_id": run_id})
    else:
        validated_output = res

    # Dataproduct Commit an den Knowledge Graph
    commit_res = commit_dataproduct(validated_output)

    return {
        "status": "completed",
        "workflow_id": workflow_id,
        "run_id": run_id,
        "input_dp": validated_input.model_dump(mode="json"),
        "output_dp": validated_output.model_dump(mode="json"),
        "commit": commit_res,
    }
