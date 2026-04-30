"""ReleaseDependencyPins: internal dep version pins after release bump."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ...types.pin import Pin
from .release_bump_versions import ReleaseBumpVersions
from ..shared.workspace_packages import WorkspacePackages
from ...utils.versioning import compute_dependency_pins


@singleton
class ReleaseDependencyPins(Frozen):
    """Pins to apply after post-release version bumping."""

    items: list[Pin] = []


@provider(ReleaseDependencyPins)
def provide_release_dependency_pins(
    bump_versions: ReleaseBumpVersions,
    workspace_packages: WorkspacePackages,
) -> ReleaseDependencyPins:
    # Update internal dep version ranges to match next-dev versions.
    pins = compute_dependency_pins(bump_versions.items, workspace_packages.items)
    return ReleaseDependencyPins(items=pins)
