"""WorkflowState: current state of the workflow file on disk."""

from __future__ import annotations

from pathlib import Path

from diny import singleton, provider

from ...types.base import Frozen
from .git_repo import GitRepo
from ..params.workflow_params import WorkflowParams


@singleton
class WorkflowState(Frozen):
    """The current workflow file state: content, existence, merge base."""

    file_path: str = ""
    exists: bool = False
    content: str = ""
    merge_base: str = ""
    is_dirty: bool = False


@provider(WorkflowState)
def provide_workflow_state(
    params: WorkflowParams,
    git_repo: GitRepo,
) -> WorkflowState:
    workflow_path = Path(params.workflow_dir) / "release.yml"
    file_path = str(workflow_path)
    exists = workflow_path.exists()
    content = workflow_path.read_text() if exists else ""

    base_path = Path(".uvr") / "bases" / file_path
    merge_base = base_path.read_text() if base_path.exists() else ""

    is_dirty = git_repo.file_is_dirty(file_path) if exists else False

    return WorkflowState(
        file_path=file_path,
        exists=exists,
        content=content,
        merge_base=merge_base,
        is_dirty=is_dirty,
    )
