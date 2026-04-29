"""ReleaseGuard: precondition checks before release planning."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ...types.job import Job
from ..shared.worktree import Worktree
from ..params.release_target import ReleaseTarget
from .version_fix import VersionFix


class UserRecoverableError(ValueError):
    """A guard failure that can be automatically fixed.

    Carries a Job with commands that resolve the issue. The CLI catches this,
    executes the fix (with user confirmation), then restarts the process so
    the DI container re-resolves everything from the now-corrected disk state.
    """

    def __init__(self, message: str, fix_job: Job) -> None:
        super().__init__(message)
        self.fix_job = fix_job


@singleton
class ReleaseGuard(Frozen):
    """Construction proves all release preconditions passed."""


@provider(ReleaseGuard)
def provide_release_guard(
    worktree: Worktree,
    release_target: ReleaseTarget,
    version_fix: VersionFix,
) -> ReleaseGuard:
    if worktree.is_dirty:
        raise ValueError("Working tree is dirty. Commit or stash changes first.")
    if release_target.value == "ci" and worktree.is_ahead_or_behind:
        raise ValueError("Local HEAD differs from remote. Pull or push first.")
    # Check version fix last because the fix itself commits.
    if version_fix.job.commands:
        raise UserRecoverableError(
            "Dev versions need to be stabilized before release.",
            fix_job=version_fix.job,
        )
    return ReleaseGuard()
