"""Orchestrator: resolve dependencies, apply intent, return plan."""

from __future__ import annotations

from typing import Any

from diny import inject, provide

from .states.uvr_state import UvrState
from .states.workflow import WorkflowState
from .states.workspace import Workspace
from .types import (
    Hooks,
    Plan,
    PlanMetadata,
)


def compute_plan(intent: Any) -> Plan:
    """Single entry point. CLI calls this.

    All dependencies are resolved by diny. Each call gets a fresh
    scope so singletons are not shared across calls. Callers that
    need custom PlanParams wrap this call in provide(params).
    """
    with provide():
        return _run(intent)


@inject
def _run(
    intent: Any,
    *,
    workspace: Workspace,
    uvr_state: UvrState,
    workflow_state: WorkflowState,
    hooks: Hooks,
) -> Plan:
    if hooks:
        intent = hooks.pre_plan(workspace, intent)

    inject(intent.guard)()
    result = inject(intent.plan)()

    if hooks:
        result = hooks.post_plan(workspace, intent, result)

    metadata = PlanMetadata(
        workspace=workspace,
        uvr_state=uvr_state,
        workflow_state=workflow_state,
    )
    return result.model_copy(update={"metadata": metadata})
