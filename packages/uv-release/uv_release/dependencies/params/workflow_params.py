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
    print_template: bool = False
    workflow_dir: str = ".github/workflows"
    editor: str = ""
    show_diff: bool = False
    # One-shot override for the three-way merge baseline. Used when
    # `[tool.uvr.config].workflow-version` is missing (workflow predates
    # version tracking) or wrong, and the user knows the version they
    # installed with.
    from_version: str = ""
