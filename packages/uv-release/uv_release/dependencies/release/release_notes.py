"""Release notes: git-generated and user-provided, merged together."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ..shared.baseline_tags import BaselineTags
from ..build.build_packages import BuildPackages
from ..shared.git_repo import GitRepo
from ..params.user_release_notes import UserReleaseNotes


@singleton
class GitReleaseNotes(Frozen):
    """Package name -> notes auto-generated from git commit log."""

    items: dict[str, str] = {}


@provider(GitReleaseNotes)
def provide_git_release_notes(
    build_packages: BuildPackages,
    baseline_tags: BaselineTags,
    git_repo: GitRepo,
) -> GitReleaseNotes:
    items: dict[str, str] = {}
    head = git_repo.head_commit()
    for name, pkg in build_packages.items.items():
        baseline = baseline_tags.items.get(name)
        if baseline is None:
            items[name] = "Initial release."
        else:
            log = git_repo.commit_log(baseline.commit, head, pkg.path)
            items[name] = log if log else "No commit log available."
    return GitReleaseNotes(items=items)


@singleton
class ReleaseNotes(Frozen):
    """Package name -> final release notes. User notes override git notes."""

    items: dict[str, str] = {}


@provider(ReleaseNotes)
def provide_release_notes(
    git_release_notes: GitReleaseNotes,
    user_release_notes: UserReleaseNotes,
) -> ReleaseNotes:
    items = dict(git_release_notes.items)
    items.update(user_release_notes.items)
    return ReleaseNotes(items=items)
