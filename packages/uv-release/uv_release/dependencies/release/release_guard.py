"""ReleaseGuard: precondition checks before release planning."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ...types.job import Job
from ...types.tag import Tag
from ..shared.git_repo import GitRepo
from ..shared.workflow_state import WorkflowState
from ..shared.worktree import Worktree
from ..params.release_target import ReleaseTarget
from .release_versions import ReleaseVersions
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
    workflow_state: WorkflowState,
    release_versions: ReleaseVersions,
    git_repo: GitRepo,
) -> ReleaseGuard:
    if not workflow_state.exists:
        raise ValueError(
            f"Workflow file not found at {workflow_state.file_path}. "
            "Run 'uvr workflow upgrade' to create it."
        )
    if worktree.is_dirty:
        raise ValueError("Working tree is dirty. Commit or stash changes first.")
    if release_target.value == "ci" and worktree.is_ahead_or_behind:
        raise ValueError("Local HEAD differs from remote. Pull or push first.")
    # Reject if any release version already has a tag.
    already_tagged = [
        f"{name} ({Tag.release_tag_name(name, ver)})"
        for name, ver in release_versions.items.items()
        if git_repo.find_tag(Tag.release_tag_name(name, ver)) is not None
    ]
    if already_tagged:
        raise ValueError(
            "Release tags already exist for: "
            + ", ".join(already_tagged)
            + ". Bump versions before releasing."
        )
    # Check version fix last because the fix itself commits.
    if version_fix.job.commands:
        raise UserRecoverableError(
            "Dev versions need to be stabilized before release.",
            fix_job=version_fix.job,
        )
    return ReleaseGuard()
