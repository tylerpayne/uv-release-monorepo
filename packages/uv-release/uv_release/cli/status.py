"""The ``uvr status`` command."""

from __future__ import annotations

import argparse

from diny import provide

from ._args import CommandArgs, compute_plan_or_exit
from ._display import format_table
from ..intents.status import StatusIntent
from ..types import PlanParams


class StatusArgs(CommandArgs):
    """Typed arguments for ``uvr status``."""

    all_packages: bool = False
    packages: list[str] | None = None


def cmd_status(args: argparse.Namespace) -> None:
    """Show workspace package status. Read-only, never modifies disk."""
    parsed = StatusArgs.from_namespace(args)

    params = PlanParams(
        all_packages=parsed.all_packages,
        packages=frozenset(parsed.packages or []),
    )
    intent = StatusIntent()
    with provide(params):
        plan = compute_plan_or_exit(intent)

    changed_map = {c.package.name: c for c in plan.changes}

    workspace = plan.metadata.workspace
    assert workspace is not None

    if not workspace.packages:
        print("No packages found.")
        return

    print()
    print("Packages")
    print("--------")

    headers = ("STATUS", "PACKAGE", "VERSION", "DIFF FROM")
    rows: list[tuple[str, ...]] = []
    for name, pkg in sorted(workspace.packages.items()):
        if name in changed_map:
            change = changed_map[name]
            reason = change.reason or "changed"
            baseline = change.baseline.raw if change.baseline else "(initial)"
        else:
            reason = "unchanged"
            baseline = ""
        rows.append((reason, name, pkg.version.raw, baseline))

    for line in format_table(headers, rows):
        print(line)

    if not changed_map:
        print()
        print("Nothing changed since last release. Use --all-packages to force.")

    print()
