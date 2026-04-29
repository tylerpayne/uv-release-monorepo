"""Shared fixtures and helpers for CLI behavioral tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

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


def tag_all(cwd: Path) -> None:
    """Tag both packages so they appear fully released."""
    git(cwd, "tag", "pkg-a/v0.1.0.dev0")
    git(cwd, "tag", "pkg-a/v0.1.0.dev0-base")
    git(cwd, "tag", "pkg-b/v0.1.0.dev0")
    git(cwd, "tag", "pkg-b/v0.1.0.dev0-base")


@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A two-package uv workspace with a clean git repo.

    packages/pkg-a  0.1.0.dev0  (no deps)
    packages/pkg-b  0.1.0.dev0  (depends on pkg-a)
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

    for name, deps in [("pkg-a", []), ("pkg-b", ["pkg-a>=0.1.0"])]:
        pkg = root / "packages" / name
        pkg.mkdir(parents=True)
        (pkg / "pyproject.toml").write_text(
            tomlkit.dumps(
                {
                    "project": {
                        "name": name,
                        "version": "0.1.0.dev0",
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
        mod.mkdir()
        (mod / "__init__.py").write_text("")

    git(root, "init")
    git(root, "config", "user.name", "test")
    git(root, "config", "user.email", "test@test")
    git(root, "add", ".")
    git(root, "commit", "-m", "init")

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
