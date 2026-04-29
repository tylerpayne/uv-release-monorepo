"""uvr release: plan and execute a full release."""

from __future__ import annotations

from diny import inject, resolve

from ..commands import DispatchWorkflowCommand
from ..dependencies.params.release_target import ReleaseTarget
from ..dependencies.release.plan import Plan
from ..dependencies.release.release_notes import ReleaseNotes
from ..dependencies.shared.hooks import Hooks
from ..dependencies.shared.workspace_packages import WorkspacePackages
from ..execute import execute_job, execute_plan
from ..types.job import Job
from ._cli import Params


@inject
def cmd_release(
    plan: Plan,
    params: Params,
    release_notes: ReleaseNotes,
    hooks: Hooks,
    workspace: WorkspacePackages,
) -> None:
    # --plan: execute a pre-serialized plan from CI.
    if params.plan_json:
        deserialized = Plan.model_validate_json(params.plan_json)
        execute_plan(deserialized, hooks)
        return

    plan = hooks.post_plan(workspace.root, "release", plan)

    # --json: print the plan as JSON and exit.
    if params.json_output:
        print(plan.model_dump_json(indent=2))
        return

    if not any(j.commands for j in plan.jobs):
        print("Nothing changed since last release.")
        return

    print("\nRelease plan:")
    for job in plan.jobs:
        status = f"({len(job.commands)} commands)" if job.commands else "(skip)"
        print(f"  {job.name}: {status}")

    if release_notes.items:
        print("\nRelease notes:")
        for name, notes in sorted(release_notes.items.items()):
            print(f"  {name}:")
            for line in notes.splitlines()[:5]:
                print(f"    {line}")

    if params.dry_run:
        return

    if not params.yes:
        print()
        try:
            answer = input("Proceed? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if answer != "y":
            return

    # --where ci: dispatch to GitHub Actions.
    target = resolve(ReleaseTarget)
    if target.value == "ci":
        plan_json = plan.model_dump_json()
        dispatch_job = Job(
            name="dispatch",
            commands=[
                DispatchWorkflowCommand(
                    label="Dispatch to GitHub Actions", plan_json=plan_json
                )
            ],
        )  # type: ignore[arg-type]
        execute_job(dispatch_job, hooks)
        return

    execute_plan(plan, hooks)
