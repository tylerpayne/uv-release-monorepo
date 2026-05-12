"""WorkflowUpgradeJob: scaffold or upgrade the release workflow.

Three install modes:
- no flags: scaffold if missing, error if file exists.
- --upgrade: three-way merge using the base from the previously-recorded
  workflow-version (fetched via uvx). Updates workflow-version after success.
- --force: overwrite with the current template. Updates workflow-version.

The .uvr/bases/ folder is a transient cache. The authoritative record of
"what version did the user last accept" lives in [tool.uvr.config].workflow-version
in pyproject.toml.
"""

from __future__ import annotations

from pathlib import Path

from diny import singleton, provider

from ... import ui
from ...commands import (
    AnyCommand,
    FetchWorkflowBaseCommand,
    MergeUpgradeCommand,
    UpdateTomlCommand,
    WriteFileCommand,
)
from ...types.job import Job
from ..config.uvr_config import UvrConfig
from ..params.workflow_params import WorkflowParams
from ..shared.workflow_state import WorkflowState
from ..shared.workflow_template import WorkflowTemplate


@singleton
class WorkflowUpgradeJob(Job):
    """Upgrade the release workflow file."""


# Backwards-compat fallback for users whose workflow predates
# workflow-version tracking. Picked as the first release that shipped a
# bundled workflow. Hand edits stay safe because three-way merge surfaces
# divergent regions as conflicts in the editor; only files that are
# clean upstream get the upgrade applied.
_FALLBACK_WORKFLOW_VERSION = "0.32.0"


@provider(WorkflowUpgradeJob)
def provide_workflow_upgrade_job(
    params: WorkflowParams,
    state: WorkflowState,
    template: WorkflowTemplate,
    config: UvrConfig,
) -> WorkflowUpgradeJob:
    if not template.content:
        msg = "No workflow template found. Is uv-release installed correctly?"
        raise ValueError(msg)

    # --print-template is a pure stdout dump consumed by --upgrade in a newer
    # uvr running us via uvx. Short-circuit here so we never touch the user's
    # cwd state (existence checks, mode requirements, version records). Without
    # this, fetching the base from any older uvr fails whenever the caller's
    # repo already has the workflow file installed.
    if params.print_template:
        return WorkflowUpgradeJob(name="workflow-upgrade", commands=[])

    commands: list[AnyCommand] = []
    base_path = str(Path(".uvr") / "bases" / state.file_path)

    # Scaffold path: file missing, just write it and record the version.
    if not state.exists:
        commands.append(
            WriteFileCommand(
                label=f"Write {state.file_path}",
                path=state.file_path,
                content=template.content,
            )
        )
        commands.append(
            UpdateTomlCommand(
                label=f"Record workflow-version={template.version}",
                key="workflow-version",
                value=template.version,
            )
        )
        return WorkflowUpgradeJob(name="workflow-upgrade", commands=commands)

    # File exists. Bare `install` is a no-op error; user must pick a mode.
    if not params.upgrade and not params.force:
        msg = (
            f"{state.file_path} already exists. "
            "Use --upgrade to three-way-merge with the bundled template, "
            "or --force to overwrite."
        )
        raise ValueError(msg)

    if state.is_dirty and not params.force:
        msg = f"{state.file_path} has uncommitted changes. Commit first or use --force."
        raise ValueError(msg)

    if params.upgrade:
        # Resolve the merge baseline in priority order:
        #   1. --from-version flag (one-shot override the user just typed)
        #   2. [tool.uvr.config].workflow-version (recorded after --upgrade)
        #   3. _FALLBACK_WORKFLOW_VERSION (oldest known baseline; preserves
        #      hand edits via merge conflicts)
        from_version = params.from_version or config.workflow_version
        if not from_version:
            from_version = _FALLBACK_WORKFLOW_VERSION
            ui.console.print(
                "  [yellow]No workflow-version recorded; falling back to "
                f"uv-release {from_version} as the merge baseline.[/]"
            )
            ui.console.print(
                "  [yellow]Hand edits stay safe — divergent regions land "
                "in your editor as conflicts. Override with [/]"
                "[uvr.cmd]--from-version VERSION[/][yellow].[/]"
            )
        commands.append(
            FetchWorkflowBaseCommand(
                label=f"Fetch base from uv-release {from_version}",
                from_version=from_version,
                output_path=base_path,
            )
        )
        commands.append(
            MergeUpgradeCommand(
                label=f"Upgrade {state.file_path}",
                file_path=state.file_path,
                base_path=base_path,
                incoming_content=template.content,
                editor=params.editor,
            )
        )
        commands.append(
            UpdateTomlCommand(
                label=f"Record workflow-version={template.version}",
                key="workflow-version",
                value=template.version,
            )
        )
        return WorkflowUpgradeJob(name="workflow-upgrade", commands=commands)

    # --force: overwrite and record version.
    commands.append(
        WriteFileCommand(
            label=f"Overwrite {state.file_path}",
            path=state.file_path,
            content=template.content,
        )
    )
    commands.append(
        UpdateTomlCommand(
            label=f"Record workflow-version={template.version}",
            key="workflow-version",
            value=template.version,
        )
    )
    return WorkflowUpgradeJob(name="workflow-upgrade", commands=commands)
