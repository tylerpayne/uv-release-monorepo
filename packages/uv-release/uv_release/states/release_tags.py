"""Resolve verified release tags for unchanged packages."""

from __future__ import annotations

from packaging.version import InvalidVersion
from packaging.version import Version as PkgVersion
from pydantic import Field

from diny import provider

from ..utils.git import GitRepo
from ..types import Tag
from .base import State
from .workspace import Workspace


class ReleaseTags(State):
    """Verified release tags for unchanged packages, resolved from git."""

    tags: dict[str, str] = Field(default_factory=dict)


@provider(ReleaseTags)
def parse_release_tags(workspace: Workspace, git_repo: GitRepo) -> ReleaseTags:
    """Find release tags that exist in git for each package."""
    tags: dict[str, str] = {}
    for name, pkg in workspace.packages.items():
        if pkg.version.is_dev:
            tag_name = _find_latest_release_tag(name, git_repo)
            if tag_name is not None:
                tags[name] = tag_name
            continue
        tag_name = Tag.release_tag_name(name, pkg.version)
        if git_repo.find_tag(tag_name) is not None:
            tags[name] = tag_name
    return ReleaseTags(tags=tags)


def _find_latest_release_tag(name: str, repo: GitRepo) -> str | None:
    """Find the latest non-dev release tag for a package."""
    prefix = Tag.tag_prefix(name)
    candidates: list[tuple[PkgVersion, str]] = []
    for tag_name in repo.list_tags(prefix):
        if Tag.is_baseline_tag_name(tag_name):
            continue
        ver_str = tag_name[len(prefix) :]
        try:
            pv = PkgVersion(ver_str)
        except InvalidVersion:
            continue
        if pv.is_devrelease:
            continue
        candidates.append((pv, tag_name))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]
