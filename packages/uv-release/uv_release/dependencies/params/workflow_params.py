"""WorkflowParams: parameters for workflow subcommands."""

from __future__ import annotations

from diny import singleton

from ...types.base import Frozen


@singleton
class WorkflowParams(Frozen):
    """Seeded by CLI. Controls workflow validate/upgrade behavior."""

    subcommand: str = ""
    force: bool = False
    upgrade: bool = False
    base_only: bool = False
    workflow_dir: str = ".github/workflows"
    editor: str = ""
    show_diff: bool = False
