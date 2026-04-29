"""ReleaseTags: latest release tags for workspace packages."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from .git_repo import GitRepo
from .workspace_packages import WorkspacePackages


@singleton
class ReleaseTags(Frozen):
    """Package name -> latest release tag name. Only packages with actual releases."""

    items: dict[str, str] = {}


@provider(ReleaseTags)
def provide_release_tags(
    workspace_packages: WorkspacePackages,
    git_repo: GitRepo,
) -> ReleaseTags:
    items: dict[str, str] = {}
    for name in workspace_packages.items:
        tag_name = git_repo.find_latest_release_tag(name)
        if tag_name is not None:
            items[name] = tag_name
    return ReleaseTags(items=items)
