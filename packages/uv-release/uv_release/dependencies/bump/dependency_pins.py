"""BumpDependencyPins: internal dep version pins after standalone bump."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ...types.pin import Pin
from .bump_versions import BumpVersions
from ..shared.workspace_packages import WorkspacePackages
from ...utils.versioning import compute_dependency_pins


@singleton
class BumpDependencyPins(Frozen):
    """Pins to apply after standalone version bumping."""

    items: list[Pin] = []


@provider(BumpDependencyPins)
def provide_bump_dependency_pins(
    bump_versions: BumpVersions,
    workspace_packages: WorkspacePackages,
) -> BumpDependencyPins:
    # Update internal dep version ranges to match bumped versions.
    pins = compute_dependency_pins(bump_versions.items, workspace_packages.items)
    return BumpDependencyPins(items=pins)
