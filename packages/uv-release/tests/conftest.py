"""Shared fixtures and helpers for CLI behavioral tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import diny
import pytest
import tomlkit


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


def git_head(cwd: Path) -> str:
    return git(cwd, "rev-parse", "HEAD").stdout.strip()


def read_toml(path: Path) -> dict:
    return tomlkit.loads(path.read_text())


def run_cli(*argv: str) -> None:
    """Set sys.argv and invoke cli().  Must run inside diny.provide()."""
    import sys

    sys.argv = ["uvr", *argv]
    from uv_release.cli._cli import cli

    cli()


def get_plan_json(*argv: str) -> dict:
    """Run release --json and return the parsed plan."""
    import sys
    from io import StringIO

    sys.argv = ["uvr", "release", "--json", "--where", "local", *argv]
    old_stdout = sys.stdout
    sys.stdout = buf = StringIO()
    try:
        from uv_release.cli._cli import cli

        cli()
    finally:
        sys.stdout = old_stdout
    return json.loads(buf.getvalue())


def tag_all(cwd: Path) -> None:
    """Tag both packages so they appear fully released."""
    git(cwd, "tag", "pkg-a/v0.1.0.dev0")
    git(cwd, "tag", "pkg-a/v0.1.0.dev0-base")
    git(cwd, "tag", "pkg-b/v0.1.0.dev0")
    git(cwd, "tag", "pkg-b/v0.1.0.dev0-base")


def _make_package(
    root: Path, name: str, version: str, deps: list[str]
) -> None:
    pkg = root / "packages" / name
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "pyproject.toml").write_text(
        tomlkit.dumps(
            {
                "project": {
                    "name": name,
                    "version": version,
                    "dependencies": deps,
                },
                "build-system": {
                    "requires": ["hatchling"],
                    "build-backend": "hatchling.build",
                },
            }
        )
    )
    mod = pkg / name.replace("-", "_")
    mod.mkdir(exist_ok=True)
    (mod / "__init__.py").write_text("")


@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A two-package uv workspace with a clean git repo.

    packages/pkg-a  0.1.0.dev0  (no deps)
    packages/pkg-b  0.1.0.dev0  (depends on pkg-a)

    Both are untagged (initial release).
    """
    root = tmp_path

    (root / "pyproject.toml").write_text(
        tomlkit.dumps(
            {
                "tool": {
                    "uv": {"workspace": {"members": ["packages/*"]}},
                    "uvr": {
                        "config": {"latest": "pkg-a", "python_version": "3.12"},
                    },
                },
            }
        )
    )

    _make_package(root, "pkg-a", "0.1.0.dev0", [])
    _make_package(root, "pkg-b", "0.1.0.dev0", ["pkg-a>=0.1.0"])

    git(root, "init")
    git(root, "config", "user.name", "test")
    git(root, "config", "user.email", "test@test")
    git(root, "add", ".")
    git(root, "commit", "-m", "init")

    monkeypatch.chdir(root)
    return root


@pytest.fixture()
def released_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Three-package workspace where pkg-a is already released.

    packages/pkg-a  1.0.1.dev0  (released at 1.0.0, now in next dev cycle)
    packages/pkg-b  0.1.0.dev0  (depends on pkg-a, unreleased)
    packages/pkg-c  0.1.0.dev0  (depends on pkg-b, unreleased)

    pkg-a has a release tag and a baseline tag for its dev cycle. Change
    detection finds no changes in pkg-a (no commits since baseline). pkg-b
    and pkg-c are both new (no tags) so they are build targets. This exercises:
    - Released dep download to deps/
    - Multi-layer topo sort (pkg-b layer 0, pkg-c layer 1)
    - Dependency propagation
    - Release/publish job structure with wheel attachment
    """
    root = tmp_path

    (root / "pyproject.toml").write_text(
        tomlkit.dumps(
            {
                "tool": {
                    "uv": {"workspace": {"members": ["packages/*"]}},
                    "uvr": {
                        "config": {"latest": "pkg-c", "python_version": "3.12"},
                        "publish": {"index": "pypi", "environment": "release"},
                    },
                },
            }
        )
    )

    _make_package(root, "pkg-a", "1.0.1.dev0", [])
    _make_package(root, "pkg-b", "0.1.0.dev0", ["pkg-a>=1.0.0"])
    _make_package(root, "pkg-c", "0.1.0.dev0", ["pkg-b>=0.1.0"])

    git(root, "init")
    git(root, "config", "user.name", "test")
    git(root, "config", "user.email", "test@test")
    git(root, "add", ".")
    git(root, "commit", "-m", "init")

    # pkg-a was released at 1.0.0, then bumped to 1.0.1.dev0 with a baseline.
    git(root, "tag", "pkg-a/v1.0.0")
    git(root, "tag", "pkg-a/v1.0.1.dev0-base")

    monkeypatch.chdir(root)
    return root


@pytest.fixture()
def mock_builds(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Mock uv build so BuildCommand succeeds without actually building."""
    calls: list[list[str]] = []
    _real = subprocess.run

    def _patched(args: str | list[str], **kwargs):  # type: ignore[no-untyped-def]
        if (
            isinstance(args, list)
            and len(args) >= 2
            and args[0] == "uv"
            and args[1] == "build"
        ):
            calls.append(list(args))
            return subprocess.CompletedProcess(args, 0)
        return _real(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", _patched)
    return calls
