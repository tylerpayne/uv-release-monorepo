"""RepositoryContext: pre-fetched repository state for release planning."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
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
    - ``rebuild_all``: skip baseline scanning (all packages are dirty)
    - ``release_type == "final" | "dev"``: skip full tag scan
      (only pre/post need ``next_pre_number``/``next_post_number``)
    - No packages: skip everything after discovery
    - GitHub releases: fetched in parallel with baselines, ETag-cached
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

    tag_prefixes = [f"{name}/v" for name in packages]

    # Baselines: skip if rebuild_all (everything is dirty anyway)
    if config.rebuild_all:
        baselines: dict[str, str | None] = {name: None for name in packages}
        if progress:
            progress.complete("Skipped baselines (--rebuild-all)")
    else:
        # Scan tags for baseline checking
        if progress:
            progress.update("Scanning git tags")
        all_git_tags = list_tags(repo, prefixes=tag_prefixes)
        git_tags_for_baselines = set(all_git_tags)
        if progress:
            progress.complete(f"Scanned {len(git_tags_for_baselines)} git tags")

        if progress:
            progress.update("Finding baselines")
        baselines = find_baseline_tags(packages, all_tags=git_tags_for_baselines)
        baselined = sum(1 for b in baselines.values() if b)
        if progress:
            progress.complete(f"Found {baselined} baselines")

    # GitHub releases: fetch (cached via ETag) in parallel with
    # full tag scan if needed for pre/post version numbering
    needs_full_tags = config.release_type in ("pre", "post")

    if progress:
        progress.update("Scanning GitHub releases")

    if needs_full_tags:
        # Pre/post releases need all package tags for next_pre_number/next_post_number
        with ThreadPoolExecutor(max_workers=2) as pool:
            releases_future = pool.submit(list_release_tag_names)
            tags_future = pool.submit(list_tags, repo, prefixes=tag_prefixes)
            github_releases = releases_future.result()
            git_tags = set(tags_future.result())
        if progress:
            progress.complete(
                f"Scanned {len(github_releases)} releases, {len(git_tags)} tags"
            )
    else:
        # Final/dev releases only need GitHub releases for release tag matching
        github_releases = list_release_tag_names()
        # Use baseline tags if we already scanned them, otherwise minimal scan
        git_tags = git_tags_for_baselines if not config.rebuild_all else set()
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
