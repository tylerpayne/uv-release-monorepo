"""CI workflow job commands (``uvr jobs validate/build/release/bump``)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ._common import _resolve_plan_json
from ..shared.models import ReleasePlan
from ..shared.executor import ReleaseExecutor
from ..shared.hooks import load_hook


def cmd_validate_plan(args: argparse.Namespace) -> None:
    """Validate and pretty-print the release plan."""
    plan = ReleasePlan.model_validate_json(_resolve_plan_json(args.plan))
    print(json.dumps(plan.model_dump(mode="json"), indent=2))


def cmd_build(args: argparse.Namespace) -> None:
    """Build packages for a runner."""
    plan_obj = ReleasePlan.model_validate_json(_resolve_plan_json(args.plan))
    hook = load_hook(Path.cwd())
    ReleaseExecutor(plan_obj, hook).build(runner=args.runner)


def cmd_release(args: argparse.Namespace) -> None:
    """Tag, create GitHub releases, and push release tags."""
    plan_obj = ReleasePlan.model_validate_json(_resolve_plan_json(args.plan))
    hook = load_hook(Path.cwd())
    ReleaseExecutor(plan_obj, hook).publish()


def cmd_bump(args: argparse.Namespace) -> None:
    """Bump versions, commit, baseline tags, and push."""
    plan_obj = ReleasePlan.model_validate_json(_resolve_plan_json(args.plan))
    hook = load_hook(Path.cwd())
    ReleaseExecutor(plan_obj, hook).bump()
