"""The ``uvr hooks`` command -- thin wrapper over the shared YAML CRUD engine."""

from __future__ import annotations

import argparse
from pathlib import Path

from ._common import _fatal
from ._yaml import _yaml_get, _MISSING
from .workflow import _load_yaml, _yaml_crud

_HOOK_JOB_DEFAULTS = {
    "runs-on": "ubuntu-latest",
    "steps": [{"name": "Echo", "run": 'echo "No-op"'}],
}
"""Default scaffold for a new hook job."""


def cmd_hooks(args: argparse.Namespace) -> None:
    """Manage CI hook jobs via jq-style paths.

    Translates ``uvr hooks PHASE [.path]`` to ``uvr workflow .jobs.PHASE[.path]``
    and delegates to the shared CRUD engine.
    """
    root = Path.cwd()
    workflow_dir = getattr(args, "workflow_dir", ".github/workflows")
    release_yml = root / workflow_dir / "release.yml"
    if not release_yml.exists():
        _fatal("No release.yml found. Run `uvr init` first to generate the workflow.")

    phase: str = args.phase
    subpath: str = getattr(args, "path", None) or ""

    # Build full path: .jobs.<phase>[<subpath>]
    full_path = f".jobs.{phase}{subpath}"
    args.path = full_path

    doc = _load_yaml(release_yml)

    # Ensure the hook job exists with required scaffold before any mutation
    job = _yaml_get(doc, ["jobs", phase])
    if job is _MISSING:
        if not isinstance(doc.get("jobs"), dict):
            doc["jobs"] = {}
        doc["jobs"][phase] = dict(_HOOK_JOB_DEFAULTS)

    _yaml_crud(release_yml, doc, args)
