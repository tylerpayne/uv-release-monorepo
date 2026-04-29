"""uvr jobs: execute a single job from a serialized plan (used by CI)."""

from __future__ import annotations

import os
import sys

from diny import inject

from ..dependencies.release.plan import Plan
from ..dependencies.shared.hooks import Hooks
from ..execute import execute_job
from ._cli import ParsedArgs


@inject
def cmd_jobs(args: ParsedArgs, hooks: Hooks) -> None:
    job_name = args.values.get("job_name", "")
    if not job_name:
        print("Usage: uvrd jobs <job_name>", file=sys.stderr)
        sys.exit(1)

    plan_json = os.environ.get("UVR_PLAN", "")
    if not plan_json:
        print("ERROR: UVR_PLAN environment variable not set.", file=sys.stderr)
        sys.exit(1)

    plan = Plan.model_validate_json(plan_json)

    job = None
    for j in plan.jobs:
        if j.name == job_name:
            job = j
            break

    if job is None:
        available = [j.name for j in plan.jobs]
        print(
            f"ERROR: Job '{job_name}' not found. Available: {', '.join(available)}",
            file=sys.stderr,
        )
        sys.exit(1)

    if job.name in plan.skip:
        print(f"Job '{job_name}' is skipped.")
        return

    execute_job(job, hooks)
