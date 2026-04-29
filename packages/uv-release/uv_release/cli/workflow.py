"""uvr workflow: dispatch to validate or upgrade subcommands."""

from __future__ import annotations

import sys

from diny import inject

from ..dependencies.params.workflow_params import WorkflowParams


@inject
def cmd_workflow(params: WorkflowParams) -> None:
    match params.subcommand:
        case "validate":
            from .workflow_validate import cmd_workflow_validate

            cmd_workflow_validate()
        case "upgrade":
            from .workflow_upgrade import cmd_workflow_upgrade

            cmd_workflow_upgrade()
        case _:
            print("Usage: uvrd workflow {validate,upgrade}")
            sys.exit(1)
