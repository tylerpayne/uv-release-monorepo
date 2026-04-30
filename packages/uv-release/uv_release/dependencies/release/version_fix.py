"""StripDev: remove .devN suffixes from versions before a non-dev release.

When `uvr release` (without --dev) detects dev versions, the ReleaseGuard
raises a UserRecoverableError carrying this fix Job. The CLI executes the
fix locally with user confirmation, then restarts so the DI container
re-resolves from the updated pyproject.toml versions. Nothing here runs
in CI. The release command never modifies versions itself. It only reads
the current git state and plans from it.
"""

from __future__ import annotations

from pydantic import Field

from diny import singleton, provider

from ...types.base import Frozen
from ...commands import (
    CommitCommand,
    PinDepsCommand,
    PushCommand,
    SetVersionCommand,
    SyncLockfileCommand,
)
from ...types.job import Job
from ..build.build_packages import BuildPackages
from ..params.dev_release import DevRelease
from ..params.release_target import ReleaseTarget
from ...utils.versioning import compute_dependency_pins, compute_release_version
from ..shared.workspace_packages import WorkspacePackages
from ...types.version import Version


@singleton
class StripDev(Frozen):
    """Commands to strip .devN suffixes before release.

    Empty job means versions are already non-dev. Non-empty job is executed
    locally by the CLI (with user confirmation) before the release plan is
    computed.
    """

    job: Job = Field(default_factory=lambda: Job(name="strip-dev"))


@provider(StripDev)
def provide_strip_dev(
    build_packages: BuildPackages,
    dev_release: DevRelease,
    workspace_packages: WorkspacePackages,
    release_target: ReleaseTarget,
) -> StripDev:
    if dev_release.value:
        return StripDev()

    # Find packages whose current version has a .devN suffix.
    needs_strip: dict[str, tuple[str, Version]] = {}
    for name, pkg in build_packages.items.items():
        release_version = compute_release_version(pkg.version)
        if pkg.version.raw != release_version.raw:
            needs_strip[name] = (pkg.path, release_version)

    if not needs_strip:
        return StripDev()

    commands: list[
        SetVersionCommand
        | PinDepsCommand
        | SyncLockfileCommand
        | CommitCommand
        | PushCommand
    ] = []

    for name, (path, version) in needs_strip.items():
        commands.append(
            SetVersionCommand(
                label=f"Set {name} to {version.raw}",
                package_path=path,
                version=version.raw,
            )
        )

    release_versions = {name: ver for name, (_, ver) in needs_strip.items()}
    pins = compute_dependency_pins(release_versions, workspace_packages.items)
    for pin in pins:
        commands.append(
            PinDepsCommand(
                label=f"Pin deps in {pin.package_path}",
                package_path=pin.package_path,
                pins=pin.pins,
            )
        )

    commands.append(SyncLockfileCommand(label="Sync lockfile"))

    body_lines = [f"  {n}: {v.raw}" for n, (_, v) in needs_strip.items()]
    commands.append(
        CommitCommand(
            label="Commit release versions",
            message="chore: set release versions",
            body="\n".join(body_lines),
        )
    )

    if release_target.value == "ci":
        commands.append(PushCommand(label="Push", follow_tags=False))

    return StripDev(job=Job(name="strip-dev", commands=commands))  # type: ignore[arg-type]
