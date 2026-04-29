"""ReleaseJob: create tags and GitHub releases."""

from __future__ import annotations

from diny import singleton, provider

from ..build.build_packages import BuildPackages
from ...commands import (
    ConfigureGitIdentityCommand,
    CreateReleaseCommand,
    CreateTagCommand,
    ShellCommand,
)
from ...types.job import Job
from .release_notes import ReleaseNotes
from ..params.reuse_releases import ReuseReleases
from ..params.skip_jobs import SkipJobs
from .release_versions import ReleaseVersions
from ...types.tag import Tag
from ..config.uvr_config import UvrConfig


@singleton
class ReleaseJob(Job):
    """Release job: create tags and GitHub releases."""


@provider(ReleaseJob)
def provide_release_job(
    build_packages: BuildPackages,
    release_versions: ReleaseVersions,
    release_notes: ReleaseNotes,
    uvr_config: UvrConfig,
    reuse_releases: ReuseReleases,
    skip_jobs: SkipJobs,
) -> ReleaseJob:
    if not build_packages.items or "release" in skip_jobs.value or reuse_releases.value:
        return ReleaseJob(name="release")

    commands: list[
        ConfigureGitIdentityCommand
        | CreateTagCommand
        | ShellCommand
        | CreateReleaseCommand
    ] = []

    commands.append(ConfigureGitIdentityCommand(label="Configure git identity"))

    for name in build_packages.items:
        version = release_versions.items[name]
        tag_name = Tag.release_tag_name(name, version)
        commands.append(CreateTagCommand(label=f"Tag {tag_name}", tag_name=tag_name))

    commands.append(ShellCommand(label="Push tags", args=["git", "push", "--tags"]))

    # Create latest_package last so GitHub marks it as "Latest".
    non_latest = [
        (n, v)
        for n, v in release_versions.items.items()
        if n != uvr_config.latest_package
    ]
    latest = [
        (n, v)
        for n, v in release_versions.items.items()
        if n == uvr_config.latest_package
    ]

    for name, version in non_latest + latest:
        tag_name = Tag.release_tag_name(name, version)
        notes = release_notes.items.get(name, "")
        commands.append(
            CreateReleaseCommand(
                label=f"Release {name} {version.raw}",
                tag_name=tag_name,
                title=f"{name} {version.raw}",
                notes=notes,
                make_latest=(name == uvr_config.latest_package),
            )
        )

    return ReleaseJob(name="release", commands=commands)  # type: ignore[arg-type]
