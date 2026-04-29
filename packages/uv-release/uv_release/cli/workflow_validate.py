"""uvr workflow validate: check workflow against template."""

from __future__ import annotations

import difflib

import yaml
from diny import inject

from ..dependencies.params.workflow_params import WorkflowParams
from ..dependencies.shared.workflow_state import WorkflowState
from ..dependencies.shared.workflow_template import WorkflowTemplate


@inject
def cmd_workflow_validate(
    params: WorkflowParams,
    state: WorkflowState,
    template: WorkflowTemplate,
) -> None:
    if not state.exists:
        print("ERROR: Workflow file does not exist.")
        print(f"  Expected: {state.file_path}")
        print("  Run 'uvrd workflow upgrade' to create it.")
        return

    errors: list[str] = []
    warnings: list[str] = []

    try:
        doc = yaml.safe_load(state.content)
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in {state.file_path}: {e}")
        return

    if not isinstance(doc, dict):
        print(f"ERROR: {state.file_path} is not a valid workflow (expected mapping).")
        return

    jobs = doc.get("jobs", {})
    required_jobs = ["validate", "build", "release", "publish", "bump"]
    for job_name in required_jobs:
        if job_name not in jobs:
            errors.append(f"Required job '{job_name}' is missing.")

    if template.content and state.content.strip() != template.content.strip():
        warnings.append("Workflow differs from bundled template.")

    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")
    if not errors and not warnings:
        print("Workflow is valid.")

    if params.show_diff and template.content:
        diff = difflib.unified_diff(
            template.content.splitlines(keepends=True),
            state.content.splitlines(keepends=True),
            fromfile="template",
            tofile=state.file_path,
        )
        diff_text = "".join(diff)
        if diff_text:
            print(f"\nDiff from template:\n{diff_text}")
        else:
            print("\nNo diff from template.")
