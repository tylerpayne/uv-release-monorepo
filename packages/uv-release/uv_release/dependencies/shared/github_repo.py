"""GitHubRepo: GitHub repository identity for gh CLI commands."""

from __future__ import annotations

import subprocess
from urllib.parse import urlparse

from diny import singleton, provider

from ...types.base import Frozen
from .git_repo import GitRepo


@singleton
class GitHubRepo(Frozen):
    """The GitHub owner/repo for this workspace, parsed from the git remote."""

    name: str = ""


@provider(GitHubRepo)
def provide_github_repo(git_repo: GitRepo) -> GitHubRepo:
    # Parse owner/repo from origin URL (HTTPS or SSH).
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        url = result.stdout.strip()
        if ":" in url and "@" in url:
            path = url.split(":")[-1]
        else:
            path = urlparse(url).path.lstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return GitHubRepo(name=path)
    except (subprocess.CalledProcessError, OSError):
        return GitHubRepo()
