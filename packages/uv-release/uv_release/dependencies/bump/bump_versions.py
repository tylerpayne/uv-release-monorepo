"""BumpVersions: versions from standalone `uvr bump`."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ..build.build_packages import BuildPackages
from ..params.bump_type import BumpType
from ...types.version import Version
from ...utils.versioning import compute_bumped_version


@singleton
class BumpVersions(Frozen):
    """Package name -> bumped version (standalone bump)."""

    items: dict[str, Version]


@provider(BumpVersions)
def provide_bump_versions(
    build_packages: BuildPackages,
    bump_type: BumpType,
) -> BumpVersions:
    items: dict[str, Version] = {}
    for name, pkg in build_packages.items.items():
        items[name] = compute_bumped_version(pkg.version, bump_type.value)
    return BumpVersions(items=items)
