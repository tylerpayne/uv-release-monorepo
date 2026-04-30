"""PublishPackages: subset of releases to publish to an index."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from .release_versions import ReleaseVersions
from ..config.uvr_config import UvrConfig
from ..config.uvr_publishing import UvrPublishing
from ...types.version import Version


@singleton
class PublishPackages(Frozen):
    """Package name -> version to publish."""

    items: dict[str, Version]


@provider(PublishPackages)
def provide_publish_packages(
    release_versions: ReleaseVersions,
    uvr_publishing: UvrPublishing,
    uvr_config: UvrConfig,
) -> PublishPackages:
    # No index configured = publishing disabled.
    if not uvr_publishing.index:
        return PublishPackages(items={})

    publishable = set(release_versions.items.keys())

    # Both UvrConfig and UvrPublishing filters must pass.
    if uvr_config.include:
        publishable &= uvr_config.include
    publishable -= uvr_config.exclude

    if uvr_publishing.include:
        publishable &= uvr_publishing.include
    publishable -= uvr_publishing.exclude

    items = {n: release_versions.items[n] for n in sorted(publishable)}
    return PublishPackages(items=items)
