"""uvr workflow upgrade: scaffold or upgrade the release workflow."""

from __future__ import annotations

from diny import inject

from ..dependencies.workflow.upgrade_job import WorkflowUpgradeJob
from ..execute import execute_job


@inject
def cmd_workflow_upgrade(upgrade_job: WorkflowUpgradeJob) -> None:
    if not upgrade_job.commands:
        print("Workflow is already up to date.")
        return

    execute_job(upgrade_job)
