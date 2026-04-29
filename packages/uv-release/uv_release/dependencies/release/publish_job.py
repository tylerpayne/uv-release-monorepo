"""PublishJob: publish wheels to a package index."""

from __future__ import annotations

from diny import singleton, provider

from ...commands import PublishToIndexCommand
from ...types.job import Job
from .publish_packages import PublishPackages
from ..config.uvr_publishing import UvrPublishing


@singleton
class PublishJob(Job):
    """Publish job: push wheels to index."""


@provider(PublishJob)
def provide_publish_job(
    publish_packages: PublishPackages,
    uvr_publishing: UvrPublishing,
) -> PublishJob:
    if not publish_packages.items:
        return PublishJob(name="publish")

    commands: list[PublishToIndexCommand] = []
    for name, version in publish_packages.items.items():
        commands.append(
            PublishToIndexCommand(
                label=f"Publish {name} {version.raw}",
                package_name=name,
                index=uvr_publishing.index,
            )
        )

    return PublishJob(name="publish", commands=commands)  # type: ignore[arg-type]
