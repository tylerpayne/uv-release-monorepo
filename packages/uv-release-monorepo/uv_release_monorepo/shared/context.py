"""RepositoryContext: pre-fetched repository state for release planning."""

from __future__ import annotations

from dataclasses import dataclass

import pygit2

from .git.local import list_tags, open_repo
from .git.remote import list_release_tag_names
from .models import PackageInfo, PlanConfig
from .utils.packages import find_packages
from .utils.shell import Progress
from .utils.tags import find_baseline_tags, find_release_tags


@dataclass
class RepositoryContext:
    """Pre-fetched repository state."""

    repo: pygit2.Repository
    git_tags: set[str]
    github_releases: set[str]
    packages: dict[str, PackageInfo]
    release_tags: dict[str, str | None]
    baselines: dict[str, str | None]


def build_context(
    config: PlanConfig,
    *,
    progress: Progress | None = None,
) -> RepositoryContext:
    """Fetch repository state, skipping work the planner won't need.

    Uses *config* to decide what to scan:
    - ``rebuild_all``: skip baseline lookup (all packages are dirty)
    - ``release_type == "final" | "dev"``: skip full tag scan
      (only pre/post need tag scanning for version numbering)
    - Baselines use direct pygit2 ref lookup — no tag scan needed
    - GitHub releases fetched in parallel, ETag-cached
    """
    if progress:
        progress.update("Opening repository")
    repo = open_repo()

    # Discover packages first — determines what else to scan
    if progress:
        progress.update("Discovering packages")
    packages = find_packages()
    if progress:
        progress.complete(f"Discovered {len(packages)} packages")

    if not packages:
        return RepositoryContext(
            repo=repo,
            git_tags=set(),
            github_releases=set(),
            packages=packages,
            release_tags={},
            baselines={},
        )

    # Baselines: direct ref lookup per package (O(1) each, no scan)
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

    # Git tags: only needed for pre/post releases (next_pre_number/next_post_number)
    # and tag conflict checking. For final/dev, an empty set is fine —
    # conflict checking also uses github_releases.
    needs_tag_scan = config.release_type in ("pre", "post")

    if needs_tag_scan:
        if progress:
            progress.update("Scanning git tags")
        tag_prefixes = [f"{name}/v" for name in packages]
        git_tags = set(list_tags(repo, prefixes=tag_prefixes))
        if progress:
            progress.complete(f"Scanned {len(git_tags)} git tags")
    else:
        git_tags: set[str] = set()

    # GitHub releases: ETag-cached, fetched in parallel with tag scan if needed
    if progress:
        progress.update("Scanning GitHub releases")
    github_releases = list_release_tag_names()
    if progress:
        progress.complete(f"Scanned {len(github_releases)} GitHub releases")

    # Find release tags (needs GitHub releases)
    if progress:
        progress.update("Finding release tags")
    release_tags = find_release_tags(packages, gh_releases=github_releases)
    tagged = sum(1 for t in release_tags.values() if t)
    if progress:
        progress.complete(f"Found {tagged} release tags")

    return RepositoryContext(
        repo=repo,
        git_tags=git_tags,
        github_releases=github_releases,
        packages=packages,
        release_tags=release_tags,
        baselines=baselines,
    )
