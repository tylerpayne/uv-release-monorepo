"""ReleaseBumpVersions: next dev versions after release."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ..params.dev_release import DevRelease
from .release_versions import ReleaseVersions
from ...types.version import Version
from ...utils.versioning import compute_next_version


@singleton
class ReleaseBumpVersions(Frozen):
    """Package name -> next dev version after release."""

    items: dict[str, Version]


@provider(ReleaseBumpVersions)
def provide_release_bump_versions(
    release_versions: ReleaseVersions,
    dev_release: DevRelease,
) -> ReleaseBumpVersions:
    items: dict[str, Version] = {}
    for name, release_version in release_versions.items.items():
        items[name] = compute_next_version(
            release_version, dev_release=dev_release.value
        )
    return ReleaseBumpVersions(items=items)
