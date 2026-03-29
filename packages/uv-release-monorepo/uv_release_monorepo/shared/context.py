"""RepositoryContext: pre-fetched repository state for release planning."""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field

import pygit2

from .utils.git import open_repo
from .models import PackageInfo, PlanConfig
from .utils.packages import find_packages
from .utils.shell import Progress
from .utils.tags import find_baseline_tags


@dataclass
class RepositoryContext:
    """Pre-fetched local repository state.

    Contains only data from the local repo — no network calls, no tag scans.
    Release tags are derived per-package via inverse version bump in the planner.
    """

    repo: pygit2.Repository
    packages: dict[str, PackageInfo]
    baselines: dict[str, str | None]


@dataclass
class ReleaseContext(RepositoryContext):
    """Repository state with pre-computed release tags.

    Used by tests to inject release tag data directly.
    """

    release_tags: dict[str, str | None] = dataclass_field(default_factory=dict)


def build_context(
    config: PlanConfig,
    *,
    progress: Progress | None = None,
) -> RepositoryContext:
    """Fetch local repository state — no network calls, no tag scans.

    Uses *config* to skip unnecessary work:
    - ``rebuild_all``: skip baseline lookup (all packages are dirty)
    - Baselines use direct pygit2 ref lookup — O(1) per package
    """
    if progress:
        progress.update("Discovering packages")
    repo = open_repo()
    packages = find_packages()
    if progress:
        progress.complete(f"Discovered {len(packages)} packages")

    if not packages:
        return RepositoryContext(
            repo=repo,
            packages=packages,
            baselines={},
        )

    # Baselines: direct ref lookup per package (O(1) each)
    # Skip entirely if rebuild_all (everything is dirty anyway)
    if config.rebuild_all:
        baselines: dict[str, str | None] = {name: None for name in packages}
        if progress:
            progress.complete("Skipped baselines (--rebuild-all)")
    else:
        if progress:
            progress.update("Finding baselines")
        baselines = find_baseline_tags(packages, repo=repo)
        baselined = sum(1 for b in baselines.values() if b)
        if progress:
            progress.complete(f"Found {baselined} baselines")

    return RepositoryContext(
        repo=repo,
        packages=packages,
        baselines=baselines,
    )
