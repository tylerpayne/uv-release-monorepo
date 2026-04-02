"""The ``uvr jobs bump`` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...shared.executor import ReleaseExecutor
from ...shared.hooks import load_hook
from ...shared.models import ReleasePlan
from ...shared.utils.cli import resolve_plan_json
from .._args import CommandArgs


class JobBumpArgs(CommandArgs):
    """Typed arguments for ``uvr jobs bump``."""

    plan: str | None = None


def cmd_bump(args: argparse.Namespace) -> None:
    """Bump versions, commit, baseline tags, and push."""
    parsed = JobBumpArgs.from_namespace(args)
    plan_obj = ReleasePlan.model_validate_json(resolve_plan_json(parsed.plan))
    hook = load_hook(Path.cwd())
    ReleaseExecutor(plan_obj, hook).bump()
