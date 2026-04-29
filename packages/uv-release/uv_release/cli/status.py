"""uvr status: show workspace package status."""

from __future__ import annotations

from diny import inject

from ..dependencies.shared.changed_packages import ChangedPackages
from ..dependencies.shared.workspace_packages import WorkspacePackages


@inject
def cmd_status(
    workspace_packages: WorkspacePackages,
    changed_packages: ChangedPackages,
) -> None:
    print("Packages:")
    for name, pkg in sorted(workspace_packages.items.items()):
        changed = name in changed_packages.names
        marker = " *" if changed else ""
        print(f"  {name} {pkg.version.raw}{marker}")

    if changed_packages.reasons:
        print("\nChanged:")
        for name, reason in sorted(changed_packages.reasons.items()):
            print(f"  {name}: {reason}")
            log = changed_packages.commit_logs.get(name, "")
            if log:
                for line in log.splitlines()[:5]:
                    print(f"    {line}")
    else:
        print("\nNo changes detected.")
