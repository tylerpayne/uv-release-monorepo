"""The ``uvr jobs validate`` command."""

from __future__ import annotations

import argparse
import json

from ...shared.models import ReleasePlan
from ...shared.utils.cli import resolve_plan_json
from .._args import CommandArgs


class JobValidateArgs(CommandArgs):
    """Typed arguments for ``uvr jobs validate``."""

    plan: str | None = None


def cmd_validate_plan(args: argparse.Namespace) -> None:
    """Validate and pretty-print the release plan."""
    parsed = JobValidateArgs.from_namespace(args)
    plan = ReleasePlan.model_validate_json(resolve_plan_json(parsed.plan))
    print(json.dumps(plan.model_dump(mode="json"), indent=2))
