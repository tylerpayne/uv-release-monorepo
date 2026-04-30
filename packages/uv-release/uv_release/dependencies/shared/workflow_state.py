"""WorkflowState: current state of the workflow file on disk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from diny import singleton, provider
from pydantic import Field

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
    # All job names from the workflow YAML, in definition order.
    job_names: list[str] = Field(default_factory=list)


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

    job_names = _parse_job_names(content) if content else []

    return WorkflowState(
        file_path=file_path,
        exists=exists,
        content=content,
        merge_base=merge_base,
        is_dirty=is_dirty,
        job_names=job_names,
    )


def _parse_job_names(content: str) -> list[str]:
    """Extract job names from workflow YAML content, in definition order."""
    try:
        doc: Any = yaml.safe_load(content)
    except yaml.YAMLError:
        return []
    if not isinstance(doc, dict):
        return []
    jobs = doc.get("jobs", {})
    if not isinstance(jobs, dict):
        return []
    return list(jobs.keys())
