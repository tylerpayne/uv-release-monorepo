"""The ``uvr init``, ``uvr init --upgrade``, and ``uvr validate`` commands."""

from __future__ import annotations

import argparse
import copy
import subprocess
import tempfile
from pathlib import Path

from ..shared.models import FROZEN_FIELDS, ReleaseWorkflow
from ..shared.toml import load_pyproject
from ._common import _fatal
from ._yaml import _dump_yaml, _load_yaml, _write_yaml


def cmd_init(args: argparse.Namespace) -> None:
    """Scaffold the GitHub Actions workflow into your repo."""
    root = Path.cwd()

    # Sanity checks
    if not (root / ".git").exists():
        _fatal("Not a git repository. Run from the repo root.")

    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        _fatal("No pyproject.toml found in current directory.")

    doc = load_pyproject(pyproject)
    members = doc.get("tool", {}).get("uv", {}).get("workspace", {}).get("members")
    if not members:
        _fatal(
            "No [tool.uv.workspace] members defined in pyproject.toml.\n"
            "uvr requires a uv workspace. Example:\n\n"
            "  [tool.uv.workspace]\n"
            '  members = ["packages/*"]'
        )

    # Write workflow
    dest_dir = root / args.workflow_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "release.yml"

    force = getattr(args, "force", False)
    if dest.exists() and not force:
        _fatal(
            f"{dest.relative_to(root)} already exists.\n"
            "  Use --force to overwrite, or `uvr validate` to check the existing file."
        )

    _write_yaml(dest, ReleaseWorkflow().model_dump(by_alias=True, exclude_none=True))

    print(f"\u2713 Wrote workflow to {dest.relative_to(root)}")
    print()
    print("Next steps:")
    print("  1. Edit the workflow to add your hook steps")
    print("  2. Run `uvr validate` to check your changes")
    print("  3. Commit and push the workflow file")
    print("  4. Trigger a release:")
    print("       uvr release")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate an existing release.yml against the ReleaseWorkflow model."""
    root = Path.cwd()
    workflow_dir = getattr(args, "workflow_dir", ".github/workflows")
    dest = root / workflow_dir / "release.yml"

    if not dest.exists():
        _fatal(f"No workflow found at {dest.relative_to(root)}. Run `uvr init` first.")

    import warnings

    from pydantic import ValidationError

    existing = _load_yaml(dest)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            ReleaseWorkflow.model_validate(existing)
        except ValidationError as e:
            print(f"\u2717 {dest.relative_to(root)} is invalid:\n{e}")
            raise SystemExit(1) from None

    if caught:
        print(f"\u26a0 {dest.relative_to(root)} has warnings:")
        for w in caught:
            print(f"  {w.message}")
    else:
        print(f"\u2713 {dest.relative_to(root)} is valid.")


def _merge_frozen(existing: dict, fresh: dict) -> dict:
    """Merge fresh frozen fields into an existing workflow dict.

    Returns a deep copy of *existing* with frozen fields (steps, strategy,
    if-conditions) replaced by their fresh template values.  Everything else
    — extra jobs, triggers, env, environment, concurrency, etc. — is preserved.
    """
    merged = copy.deepcopy(existing)

    for job_name, frozen_aliases in FROZEN_FIELDS.items():
        if job_name not in merged.get("jobs", {}):
            continue
        fresh_job = fresh.get("jobs", {}).get(job_name, {})
        for alias in frozen_aliases:
            if alias in fresh_job:
                merged["jobs"][job_name][alias] = copy.deepcopy(fresh_job[alias])

    # Update workflow_dispatch inputs (core contract)
    fresh_inputs = fresh.get("on", {}).get("workflow_dispatch", {}).get("inputs", {})
    if fresh_inputs:
        merged.setdefault("on", {}).setdefault("workflow_dispatch", {}).setdefault(
            "inputs", {}
        ).update(copy.deepcopy(fresh_inputs))

    # Ensure permissions includes contents: write
    fresh_perms = fresh.get("permissions", {})
    if fresh_perms:
        merged.setdefault("permissions", {}).update(fresh_perms)

    # Ensure required `needs` dependencies are present
    for job_name in ["release", "finalize"]:
        if job_name not in merged.get("jobs", {}):
            continue
        fresh_needs = fresh.get("jobs", {}).get(job_name, {}).get("needs", [])
        existing_needs = merged["jobs"][job_name].get("needs", [])
        for dep in fresh_needs:
            if dep not in existing_needs:
                existing_needs.insert(0, dep)
        if existing_needs:
            merged["jobs"][job_name]["needs"] = existing_needs

    return merged


def cmd_upgrade(args: argparse.Namespace) -> None:
    """Upgrade frozen fields in an existing release.yml."""
    root = Path.cwd()
    workflow_dir = getattr(args, "workflow_dir", ".github/workflows")
    dest = root / workflow_dir / "release.yml"

    if not dest.exists():
        _fatal(f"No workflow found at {dest.relative_to(root)}. Run `uvr init` first.")

    existing = _load_yaml(dest)
    fresh = ReleaseWorkflow().model_dump(by_alias=True, exclude_none=True)
    merged = _merge_frozen(existing, fresh)

    existing_text = dest.read_text()
    merged_text = _dump_yaml(merged)

    if existing_text.rstrip() == merged_text.rstrip():
        print("Already up to date.")
        return

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", prefix="release-upgraded-", delete=False
    ) as tmp:
        tmp.write(merged_text)
        tmp_path = Path(tmp.name)

    try:
        subprocess.run(
            ["git", "diff", "--no-index", "--color", str(dest), str(tmp_path)],
        )

        if getattr(args, "yes", False):
            dest.write_text(merged_text)
            print(f"\n\u2713 Upgraded {dest.relative_to(root)}")
        else:
            print()
            try:
                answer = input("Apply these changes? [y/N] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nAborted.")
                return
            if answer == "y":
                dest.write_text(merged_text)
                print(f"\u2713 Upgraded {dest.relative_to(root)}")
            else:
                print("No changes applied.")
                return
    finally:
        tmp_path.unlink(missing_ok=True)

    # Validate the result
    import warnings

    from pydantic import ValidationError

    reloaded = _load_yaml(dest)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            ReleaseWorkflow.model_validate(reloaded)
        except ValidationError as e:
            print(f"\n\u26a0 Upgraded file has validation errors:\n{e}")
            return

    if caught:
        for w in caught:
            print(f"\u26a0 {w.message}")
