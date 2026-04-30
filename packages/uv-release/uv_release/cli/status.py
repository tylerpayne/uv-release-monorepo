"""uvr status: show workspace package status."""

from __future__ import annotations

from diny import inject

from ..dependencies.shared.baseline_tags import BaselineTags
from ..dependencies.shared.changed_packages import ChangedPackages
from ..dependencies.shared.workspace_packages import WorkspacePackages
from ._display import format_table


@inject
def cmd_status(
    workspace_packages: WorkspacePackages,
    changed_packages: ChangedPackages,
    baseline_tags: BaselineTags,
) -> None:
    if not workspace_packages.items:
        print("No packages found.")
        return

    print()
    print("Packages")
    print("--------")

    headers = ("STATUS", "PACKAGE", "VERSION", "DIFF FROM")
    rows: list[tuple[str, ...]] = []
    for name, pkg in sorted(workspace_packages.items.items()):
        reason = changed_packages.reasons.get(name, "unchanged")
        baseline = baseline_tags.items.get(name)
        diff_from = baseline.raw if baseline else "(initial)"
        rows.append((reason, name, pkg.version.raw, diff_from))

    for line in format_table(headers, rows):
        print(line)

    if not changed_packages.reasons:
        print()
        print("Nothing changed since last release.")

    print()
