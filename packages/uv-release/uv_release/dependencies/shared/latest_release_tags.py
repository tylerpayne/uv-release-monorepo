"""LatestReleaseTags: latest release tags per package from GitHub API."""

from __future__ import annotations

import json
import subprocess

from diny import singleton, provider

from ...types.base import Frozen
from .github_repo import GitHubRepo
from .workspace_packages import WorkspacePackages


@singleton
class LatestReleaseTags(Frozen):
    """Package name -> latest release tag from GitHub API.

    Unlike ReleaseTags (which uses local git), this queries the GitHub API
    so it reflects the actual remote state. Used by download and install
    where the user wants wheels from published releases.
    """

    items: dict[str, str] = {}


@provider(LatestReleaseTags)
def provide_latest_release_tags(
    workspace_packages: WorkspacePackages,
    github_repo: GitHubRepo,
) -> LatestReleaseTags:
    if not github_repo.name:
        return LatestReleaseTags()

    try:
        result = subprocess.run(
            [
                "gh",
                "release",
                "list",
                "--repo",
                github_repo.name,
                "--limit",
                "100",
                "--json",
                "tagName",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return LatestReleaseTags()

    if result.returncode != 0:
        return LatestReleaseTags()

    try:
        releases = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        return LatestReleaseTags()

    # Releases are newest-first. First match per package is the latest.
    items: dict[str, str] = {}
    for name in workspace_packages.items:
        prefix = f"{name}/v"
        for rel in releases:
            tag = rel.get("tagName", "")
            if tag.startswith(prefix) and not tag.endswith("-base"):
                items[name] = tag
                break

    return LatestReleaseTags(items=items)
