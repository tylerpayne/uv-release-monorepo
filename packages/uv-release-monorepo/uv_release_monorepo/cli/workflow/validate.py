"""The ``uvr workflow validate`` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...shared.utils.cli import fatal
from ...shared.utils.toml import get_path, read_pyproject
from ...shared.utils.yaml import load_yaml
from .._args import CommandArgs
from .init import _check_frozen_paths, _load_template, _load_template_yaml


class WorkflowValidateArgs(CommandArgs):
    """Typed arguments for ``uvr workflow validate``."""

    workflow_dir: str = ".github/workflows"
    diff: bool = False


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate an existing release.yml against the ReleaseWorkflow model."""
    parsed = WorkflowValidateArgs.from_namespace(args)
    root = Path.cwd()
    dest = root / parsed.workflow_dir / "release.yml"

    if not dest.exists():
        fatal(
            f"No workflow found at {dest.relative_to(root)}. Run `uvr workflow init` first."
        )

    import difflib
    import warnings

    from pydantic import ValidationError

    from ...shared.models.workflow import ReleaseWorkflow

    existing = load_yaml(dest)
    rel = dest.relative_to(root)

    from ...shared.utils.cli import __version__

    # Resolve versions
    stored_version = ""
    if (root / "pyproject.toml").exists():
        stored_version = get_path(
            read_pyproject(root / "pyproject.toml"),
            "tool",
            "uvr",
            "config",
            "workflow_version",
            default="",
        )
    local_label = f"v{stored_version}" if stored_version else "unknown"

    # Header
    print(
        f"Validating worktree workflow {rel} ({local_label}) "
        f"against uvr template (v{__version__})."
    )
    print()

    # Phase 1: Structural validation via pydantic
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            ReleaseWorkflow.model_validate(existing)
        except ValidationError as e:
            print(f"FAIL: {e}")
            raise SystemExit(1) from None

    # Phase 2: Frozen-path diffing against bundled template
    template = _load_template_yaml()
    frozen_warnings = _check_frozen_paths(existing, template)
    all_warnings = [str(w.message) for w in caught] + frozen_warnings

    # Check if template content differs
    fresh_text = _load_template()
    existing_text = dest.read_text()
    has_diff = fresh_text.rstrip() != existing_text.rstrip()
    version_diff = stored_version and stored_version != __version__

    # Result
    if all_warnings:
        print(f"SUCCESS: 0 errors, {len(all_warnings)} warnings")
        print()
        print("Warnings:")
        for w in all_warnings:
            print(f"  {w}")
    else:
        print("SUCCESS: 0 errors, 0 warnings")

    # Hints
    if has_diff:
        print()
        print("  Run `uvr validate --diff` to view differences from the template.")
    if version_diff:
        print(
            f"  Run `uvr workflow init --upgrade` to update from "
            f"v{stored_version} to v{__version__}."
        )
    elif not stored_version:
        print("  Run `uvr workflow init --upgrade` to track your workflow version.")

    # --diff: show unified diff
    if parsed.diff and has_diff:
        print()
        diff = difflib.unified_diff(
            existing_text.splitlines(keepends=True),
            fresh_text.splitlines(keepends=True),
            fromfile=str(rel),
            tofile=f"template (v{__version__})",
        )
        for line in diff:
            print(line, end="")
