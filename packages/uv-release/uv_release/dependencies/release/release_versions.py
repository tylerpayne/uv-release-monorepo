"""ReleaseVersions: the version each package will be published at."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ..build.build_packages import BuildPackages
from ..params.dev_release import DevRelease
from ...types.version import Version
from ...utils.versioning import compute_release_version


@singleton
class ReleaseVersions(Frozen):
    """Package name -> version being released."""

    items: dict[str, Version]


@provider(ReleaseVersions)
def provide_release_versions(
    build_packages: BuildPackages,
    dev_release: DevRelease,
) -> ReleaseVersions:
    items: dict[str, Version] = {}
    for name, pkg in build_packages.items.items():
        items[name] = compute_release_version(
            pkg.version, dev_release=dev_release.value
        )
    return ReleaseVersions(items=items)
