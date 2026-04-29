"""Worktree: git working tree state."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from .git_repo import GitRepo


@singleton
class Worktree(Frozen):
    """Git working tree cleanliness and remote sync state."""

    is_dirty: bool = False
    is_ahead_or_behind: bool = False


@provider(Worktree)
def provide_worktree(git_repo: GitRepo) -> Worktree:
    return Worktree(
        is_dirty=git_repo.is_dirty(),
        is_ahead_or_behind=git_repo.is_ahead_or_behind(),
    )
