"""Plan: the release pipeline. Only used by `uvr release`."""

from __future__ import annotations

from pydantic import Field

from diny import singleton, provider

from ...types.base import Frozen
from ...types.release import Release
from ..build.build_job import BuildJob
from ..build.build_packages import BuildPackages
from .release_bump_job import ReleaseBumpJob
from .release_bump_versions import ReleaseBumpVersions
from .release_guard import ReleaseGuard
from ...types.job import Job
from .publish_job import PublishJob
from .release_job import ReleaseJob
from .release_versions import ReleaseVersions
from ..shared.baseline_tags import BaselineTags
from ..config.uvr_config import UvrConfig
from ..config.uvr_publishing import UvrPublishing
from ..config.uvr_runners import UvrRunners
from ..params.reuse_run import ReuseRun
from ..params.reuse_releases import ReuseReleases
from ..params.runner_filter import RunnerFilter
from ..params.skip_jobs import SkipJobs


@singleton
class Plan(Frozen):
    """The release pipeline. Contains all jobs and CI metadata."""

    jobs: list[Job] = Field(default_factory=list)
    releases: list[Release] = Field(default_factory=list)
    build_matrix: list[list[str]] = Field(default_factory=list)
    python_version: str = "3.12"
    publish_environment: str = ""
    skip: list[str] = Field(default_factory=list)
    reuse_run: str = ""
    reuse_releases: bool = False


@provider(Plan)
def provide_plan(
    build_job: BuildJob,
    release_job: ReleaseJob,
    publish_job: PublishJob,
    bump_job: ReleaseBumpJob,
    build_packages: BuildPackages,
    uvr_config: UvrConfig,
    uvr_publishing: UvrPublishing,
    uvr_runners: UvrRunners,
    release_versions: ReleaseVersions,
    bump_versions: ReleaseBumpVersions,
    baseline_tags: BaselineTags,
    reuse_run: ReuseRun,
    reuse_releases: ReuseReleases,
    runner_filter: RunnerFilter,
    skip_jobs: SkipJobs,
    # ReleaseGuard: side-effect only, raises if preconditions fail.
    release_guard: ReleaseGuard,
) -> Plan:
    # Validate is an empty job. CI uses it to confirm the plan is parseable.
    validate_job = Job(name="validate")
    jobs: list[Job] = [validate_job, build_job, release_job, publish_job, bump_job]

    # Skip user-requested jobs and empty (no-op) jobs. Validate is always
    # kept because CI uses it to confirm the plan JSON is parseable.
    skip = list(skip_jobs.value) + [
        j.name for j in jobs if not j.commands and j.name != "validate"
    ]

    # Flatten and deduplicate runner labels across all build targets.
    all_runners: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for name in build_packages.items:
        pkg_runners = uvr_runners.items.get(name, [["ubuntu-latest"]])
        for labels in pkg_runners:
            key = tuple(sorted(labels))
            if key not in seen:
                seen.add(key)
                all_runners.append(labels)
    # Filter to --runners if specified. Each CLI arg matches any runner set
    # that contains that label (e.g. --runners ubuntu-latest keeps [ubuntu-latest]).
    if runner_filter.value:
        all_runners = [
            r for r in all_runners if any(label in runner_filter.value for label in r)
        ]
    if not all_runners:
        all_runners = [["ubuntu-latest"]]

    return Plan(
        jobs=jobs,
        build_matrix=all_runners,
        python_version=uvr_config.python_version,
        publish_environment=uvr_publishing.environment,
        skip=sorted(set(skip)),
        releases=_build_releases(
            build_packages, release_versions, bump_versions, baseline_tags
        ),
        reuse_run=reuse_run.value,
        reuse_releases=reuse_releases.value,
    )


def _build_releases(
    build_packages: BuildPackages,
    release_versions: ReleaseVersions,
    bump_versions: ReleaseBumpVersions,
    baseline_tags: BaselineTags,
) -> list[Release]:
    releases: list[Release] = []
    for name in release_versions.items:
        tag = baseline_tags.items.get(name)
        releases.append(
            Release(
                name=name,
                current_version=build_packages.items[name].version,
                release_version=release_versions.items[name],
                next_version=bump_versions.items[name],
                baseline_tag=tag.raw if tag else "",
            )
        )
    return releases
