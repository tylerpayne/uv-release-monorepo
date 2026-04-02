"""The ``uvr jobs build`` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...shared.executor import ReleaseExecutor
from ...shared.hooks import load_hook
from ...shared.models import ReleasePlan
from ...shared.utils.cli import resolve_plan_json
from .._args import CommandArgs


class JobBuildArgs(CommandArgs):
    """Typed arguments for ``uvr jobs build``."""

    plan: str | None = None
    runner: str = ""


def cmd_build(args: argparse.Namespace) -> None:
    """Build packages for a runner."""
    parsed = JobBuildArgs.from_namespace(args)
    plan_obj = ReleasePlan.model_validate_json(resolve_plan_json(parsed.plan))
    hook = load_hook(Path.cwd())
    ReleaseExecutor(plan_obj, hook).build(runner=parsed.runner)
