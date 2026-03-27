"""The ``uvr init``, ``uvr init --upgrade``, and ``uvr validate`` commands."""

from __future__ import annotations

import argparse
import copy
import subprocess
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
            print(f"Invalid: {dest.relative_to(root)}\n{e}")
            raise SystemExit(1) from None

    rel = dest.relative_to(root)
    if caught:
        print(f"Valid: {rel} (0 errors, {len(caught)} warnings)\n")
        print("Warnings:")
        for w in caught:
            print(f"  {w.message}")
    else:
        print(f"Valid: {rel} (0 errors, 0 warnings)")


def _step_keys(step: dict) -> list[str]:
    """Return all candidate identity keys for a workflow step.

    A step can be identified by ``id``, ``name``, or ``uses``.  We return
    all that are present so matching works even when the fresh template adds
    an ``id`` to a step the user only has ``uses`` for.
    """
    keys: list[str] = []
    if "id" in step:
        keys.append(f"id:{step['id']}")
    if "name" in step:
        keys.append(f"name:{step['name']}")
    if "uses" in step:
        keys.append(f"uses:{step['uses']}")
    return keys


def _merge_steps(existing_steps: list[dict], fresh_steps: list[dict]) -> list[dict]:
    """Merge fresh template steps into existing steps.

    For each fresh step, if a matching step exists (by id, name, or uses),
    update it in place.  If no match, insert it at the position it appears
    in the fresh template.  Existing steps not in the fresh template are
    preserved.
    """
    merged = copy.deepcopy(existing_steps)
    # Map every candidate key to its index in merged
    existing_keys: dict[str, int] = {}
    for i, s in enumerate(merged):
        for k in _step_keys(s):
            existing_keys[k] = i

    insert_offset = 0
    matched_indices: set[int] = set()
    for fresh_idx, fresh_step in enumerate(fresh_steps):
        keys = _step_keys(fresh_step)
        idx = next((existing_keys[k] for k in keys if k in existing_keys), None)
        if idx is not None and idx not in matched_indices:
            merged[idx] = copy.deepcopy(fresh_step)
            matched_indices.add(idx)
        elif keys:
            # New step from template — insert at the corresponding position
            pos = min(fresh_idx + insert_offset, len(merged))
            merged.insert(pos, copy.deepcopy(fresh_step))
            insert_offset += 1
    return merged


def _merge_frozen(existing: dict, fresh: dict) -> dict:
    """Merge fresh frozen fields into an existing workflow dict.

    For scalar frozen fields (if, strategy, runs-on), replaces with the fresh
    value.  For ``steps``, does a step-level merge: matching steps (by name
    or uses) are updated, unmatched user steps are preserved.
    """
    merged = copy.deepcopy(existing)

    for job_name, frozen_aliases in FROZEN_FIELDS.items():
        if job_name not in merged.get("jobs", {}):
            continue
        fresh_job = fresh.get("jobs", {}).get(job_name, {})
        for alias in frozen_aliases:
            if alias not in fresh_job:
                continue
            if alias == "steps":
                merged["jobs"][job_name]["steps"] = _merge_steps(
                    merged["jobs"][job_name].get("steps", []),
                    fresh_job["steps"],
                )
            else:
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

    # Ensure release.yml has no uncommitted changes
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", str(dest)],
        capture_output=True,
    )
    if result.returncode != 0:
        _fatal(
            f"{dest.relative_to(root)} has uncommitted changes.\n"
            "  Commit or stash them before upgrading."
        )

    existing = _load_yaml(dest)
    fresh = ReleaseWorkflow().model_dump(by_alias=True, exclude_none=True)
    merged = _merge_frozen(existing, fresh)

    existing_text = dest.read_text()
    merged_text = _dump_yaml(merged)

    if existing_text.rstrip() == merged_text.rstrip():
        print("Already up to date.")
        return

    rel_dest = str(dest.relative_to(root))

    # Write merged content over the file
    dest.write_text(merged_text)

    if not getattr(args, "yes", False):
        # Interactive: let user revert hunks they don't want
        try:
            subprocess.run(["git", "checkout", "-p", "--", str(dest)])
        except KeyboardInterrupt:
            dest.write_text(existing_text)
            print("\nAborted. No changes applied.")
            return

        final_text = dest.read_text()
        if final_text.rstrip() == existing_text.rstrip():
            print("No changes applied.")
            return

        # Confirm the result (handles quit-early leaving partial state)
        try:
            answer = input("\nKeep these changes? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer != "y":
            dest.write_text(existing_text)
            print("Reverted. No changes applied.")
            return

    print(f"\u2713 Upgraded {rel_dest}")

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
