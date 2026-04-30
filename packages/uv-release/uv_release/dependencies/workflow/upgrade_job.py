"""WorkflowUpgradeJob: scaffold or upgrade the release workflow."""

from __future__ import annotations

from pathlib import Path

from diny import singleton, provider

from ...commands import MergeUpgradeCommand, WriteFileCommand
from ...types.job import Job
from ..params.workflow_params import WorkflowParams
from ..shared.workflow_state import WorkflowState
from ..shared.workflow_template import WorkflowTemplate


@singleton
class WorkflowUpgradeJob(Job):
    """Upgrade the release workflow file."""


@provider(WorkflowUpgradeJob)
def provide_workflow_upgrade_job(
    params: WorkflowParams,
    state: WorkflowState,
    template: WorkflowTemplate,
) -> WorkflowUpgradeJob:
    if not template.content:
        raise ValueError(
            "No workflow template found. Is uv-release installed correctly?"
        )

    commands: list[WriteFileCommand | MergeUpgradeCommand] = []
    base_path = str(Path(".uvr") / "bases" / state.file_path)

    if not state.exists:
        commands.append(
            WriteFileCommand(
                label=f"Write {state.file_path}",
                path=state.file_path,
                content=template.content,
            )
        )
        commands.append(
            WriteFileCommand(
                label="Write merge base", path=base_path, content=template.content
            )
        )
    elif state.is_dirty and not params.force:
        raise ValueError(
            f"{state.file_path} has uncommitted changes. Commit first or use --force."
        )
    elif params.base_only:
        commands.append(
            WriteFileCommand(
                label="Update merge base", path=base_path, content=template.content
            )
        )
    else:
        commands.append(
            MergeUpgradeCommand(
                label=f"Upgrade {state.file_path}",
                file_path=state.file_path,
                base_content=state.merge_base,
                incoming_content=template.content,
                base_path=base_path,
                editor=params.editor,
            )
        )

    return WorkflowUpgradeJob(name="workflow-upgrade", commands=commands)  # type: ignore[arg-type]
