"""BuildPackages: packages selected for building."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ..shared.changed_packages import ChangedPackages
from ...types.package import Package
from ..params.package_selection import PackageSelection
from ..config.uvr_config import UvrConfig
from ..shared.workspace_packages import WorkspacePackages


@singleton
class BuildPackages(Frozen):
    """Packages to build in this run (the release targets)."""

    items: dict[str, Package]


@provider(BuildPackages)
def provide_build_packages(
    workspace_packages: WorkspacePackages,
    changed_packages: ChangedPackages,
    package_selection: PackageSelection,
    uvr_config: UvrConfig,
) -> BuildPackages:
    # Selection: --all > --packages > auto-detect from changes.
    if package_selection.all_packages:
        items = dict(workspace_packages.items)
    elif package_selection.packages:
        items = {
            n: workspace_packages.items[n]
            for n in package_selection.packages
            if n in workspace_packages.items
        }
    else:
        items = {
            name: workspace_packages.items[name]
            for name in changed_packages.names
            if name in workspace_packages.items
        }

    # Apply include (allowlist) then exclude (denylist) filters.
    if uvr_config.include:
        items = {n: p for n, p in items.items() if n in uvr_config.include}
    items = {n: p for n, p in items.items() if n not in uvr_config.exclude}

    return BuildPackages(items=items)
