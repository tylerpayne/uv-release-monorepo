"""The ``uvr init``, ``uvr init --upgrade``, and ``uvr validate`` commands."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from ..shared.models import ReleaseWorkflow
from ..shared.toml import load_pyproject, save_pyproject
from ._common import _fatal
from ._yaml import _dump_yaml, _load_yaml, _write_yaml


def _git_commit_and_record(
    root: Path,
    files: list[str],
    message: str,
    config_key: str,
) -> None:
    """Stage *files*, commit, and store the commit hash in [tool.uvr.config].

    Prompts the user for confirmation before committing.
    """
    from ..shared.gitops import open_repo

    rel_files = [str(Path(f).relative_to(root)) for f in files]
    print()
    print("The following will be committed:")
    for f in rel_files:
        print(f"  git add {f}")
    print(f'  git commit -m "{message}"')
    print()
    try:
        answer = input("Commit? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nSkipped commit.")
        return
    if answer and answer != "y":
        print("Skipped commit.")
        return

    repo = open_repo(str(root))
    for f in rel_files:
        repo.index.add(f)
    repo.index.write()

    sig = repo.default_signature
    tree = repo.index.write_tree()
    parent = repo.head.peel().id
    commit_oid = repo.create_commit("HEAD", sig, sig, message, tree, [parent])

    # Store the commit hash in [tool.uvr.config]
    pyproject = root / "pyproject.toml"
    doc = load_pyproject(pyproject)
    tool = doc.setdefault("tool", {})
    uvr = tool.setdefault("uvr", {})
    config = uvr.setdefault("config", {})
    config[config_key] = str(commit_oid)
    save_pyproject(pyproject, doc)

    # Amend the commit to include the pyproject.toml change
    repo.index.add("pyproject.toml")
    repo.index.write()
    tree = repo.index.write_tree()
    repo.create_commit("HEAD", sig, sig, message, tree, [parent])

    print(f"OK: Committed {len(rel_files)} file(s)")


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

    print(f"OK: Wrote workflow to {dest.relative_to(root)}")

    _git_commit_and_record(
        root,
        [str(dest)],
        "chore: uvr init",
        "init_commit",
    )

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


def _get_base_text(root: Path, rel_path: str, config_key: str) -> str:
    """Retrieve the base file content from the init commit, or empty string."""
    import pygit2

    from ..shared.gitops import open_repo

    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return ""
    doc = load_pyproject(pyproject)
    commit_hex = doc.get("tool", {}).get("uvr", {}).get("config", {}).get(config_key)
    if not commit_hex:
        return ""

    try:
        repo = open_repo(str(root))
        commit = repo.get(commit_hex)
        if commit is None:
            return ""
        tree = commit.peel(pygit2.Tree) if hasattr(commit, "peel") else commit.tree
        entry = tree[rel_path]
        blob = repo.get(entry.id)
        if blob is None:
            return ""
        return blob.data.decode("utf-8")  # type: ignore[union-attr]
    except (KeyError, ValueError, AttributeError):
        return ""


def _three_way_merge(dest: Path, base_text: str, fresh_text: str) -> tuple[str, bool]:
    """Run git merge-file and return (merged_text, has_conflicts)."""
    with (
        tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", prefix="base-", delete=False
        ) as base_f,
        tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", prefix="fresh-", delete=False
        ) as fresh_f,
    ):
        base_f.write(base_text)
        base_f.flush()
        fresh_f.write(fresh_text)
        fresh_f.flush()
        base_path = Path(base_f.name)
        fresh_path = Path(fresh_f.name)

    try:
        result = subprocess.run(
            [
                "git",
                "merge-file",
                "-p",
                "-L",
                "current",
                "-L",
                "base",
                "-L",
                "template",
                str(dest),
                str(base_path),
                str(fresh_path),
            ],
            capture_output=True,
            text=True,
        )
    finally:
        base_path.unlink(missing_ok=True)
        fresh_path.unlink(missing_ok=True)

    if result.returncode > 1:
        _fatal(f"git merge-file failed:\n{result.stderr}")

    return result.stdout, result.returncode == 1


def cmd_upgrade(args: argparse.Namespace) -> None:
    """Upgrade an existing release.yml using three-way merge with git merge-file."""
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

    # Generate fresh template
    fresh_text = _dump_yaml(
        ReleaseWorkflow().model_dump(by_alias=True, exclude_none=True)
    )
    existing_text = dest.read_text()

    if existing_text.rstrip() == fresh_text.rstrip():
        print("Already up to date.")
        return

    rel_dest = str(dest.relative_to(root))

    # Get base from the init commit (if tracked), otherwise empty
    base_text = _get_base_text(root, rel_dest, "init_commit")

    merged_text, has_conflicts = _three_way_merge(dest, base_text, fresh_text)

    if merged_text.rstrip() == existing_text.rstrip():
        print("Already up to date.")
        return

    if has_conflicts:
        print(f"Merge has conflicts -- resolve markers in {rel_dest} after applying.")

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

    print(f"OK: Upgraded {rel_dest}")

    # Record the upgrade commit
    _git_commit_and_record(
        root,
        [str(dest)],
        "chore: uvr init --upgrade",
        "init_commit",
    )

    # Skip validation if conflicts remain
    if has_conflicts or "<<<<<<" in dest.read_text():
        print("  Resolve conflict markers before committing.")
        return

    # Validate the result
    import warnings

    from pydantic import ValidationError

    reloaded = _load_yaml(dest)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            ReleaseWorkflow.model_validate(reloaded)
        except ValidationError as e:
            print(f"\nUpgraded file has validation errors:\n{e}")
            return

    if caught:
        for w in caught:
            print(f"  Warning: {w.message}")
