"""uvr build: build changed packages locally."""

from __future__ import annotations

from diny import inject

from ..dependencies.build.build_job import BuildJob
from ..dependencies.shared.hooks import Hooks
from ..execute import execute_job


@inject
def cmd_build(build_job: BuildJob, hooks: Hooks) -> None:
    if not build_job.commands:
        print("Nothing to build. No packages have changed since last release.")
        return

    print("Building packages:\n")
    execute_job(build_job, hooks)
    print("\nDone.")
