"""The ``uvr jobs release`` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...shared.executor import ReleaseExecutor
from ...shared.hooks import load_hook
from ...shared.models import ReleasePlan
from ...shared.utils.cli import resolve_plan_json
from .._args import CommandArgs


class JobReleaseArgs(CommandArgs):
    """Typed arguments for ``uvr jobs release``."""

    plan: str | None = None


def cmd_release(args: argparse.Namespace) -> None:
    """Tag, create GitHub releases, and push release tags."""
    parsed = JobReleaseArgs.from_namespace(args)
    plan_obj = ReleasePlan.model_validate_json(resolve_plan_json(parsed.plan))
    hook = load_hook(Path.cwd())
    ReleaseExecutor(plan_obj, hook).publish()
