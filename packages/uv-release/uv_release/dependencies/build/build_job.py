"""BuildJob: build changed packages."""

from __future__ import annotations

from diny import singleton, provider

from .build_order import BuildOrder
from .build_packages import BuildPackages
from ...commands import BuildCommand, DownloadWheelsCommand
from ...types.job import Job
from .package_dependencies import PackageDependencies
from ..params.reuse_run import ReuseRun
from ..params.skip_jobs import SkipJobs


@singleton
class BuildJob(Job):
    """Build job for the release pipeline."""


@provider(BuildJob)
def provide_build_job(
    build_packages: BuildPackages,
    package_dependencies: PackageDependencies,
    build_order: BuildOrder,
    reuse_run: ReuseRun,
    skip_jobs: SkipJobs,
) -> BuildJob:
    # Empty job if nothing to build, skipped by user, or reusing prior run.
    if not build_packages.items or "build" in skip_jobs.value or reuse_run.value:
        return BuildJob(name="build")

    commands: list[DownloadWheelsCommand | BuildCommand] = []

    for dep in package_dependencies.released:
        commands.append(
            DownloadWheelsCommand(
                label=f"Download {dep.package_name} wheels",
                tag_name=dep.tag_name,
                pattern="*.whl",
            )
        )

    for layer in build_order.layers:
        for item in layer:
            commands.append(
                BuildCommand(
                    label=f"Build {item.name}",
                    package_path=item.package.path,
                    out_dir=item.out_dir,
                )
            )

    return BuildJob(name="build", commands=commands)  # type: ignore[arg-type]
