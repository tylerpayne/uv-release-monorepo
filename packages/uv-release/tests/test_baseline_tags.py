"""Tests for baseline tag resolution across all version states.

Uses real git repos to test each branch of _find_baseline_tag.
"""

from __future__ import annotations

from pathlib import Path

import diny
import pytest

from conftest import git, run_cli, _make_package
import tomlkit


def _workspace_with_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: str, tags: list[str]
) -> Path:
    """Create a single-package workspace at a given version with given tags."""
    root = tmp_path
    (root / "pyproject.toml").write_text(
        tomlkit.dumps(
            {
                "tool": {
                    "uv": {"workspace": {"members": ["packages/*"]}},
                    "uvr": {"config": {}},
                },
            }
        )
    )
    _make_package(root, "mylib", version, [])
    git(root, "init")
    git(root, "config", "user.name", "test")
    git(root, "config", "user.email", "test@test")
    git(root, "add", ".")
    git(root, "commit", "-m", "init")
    for tag in tags:
        git(root, "tag", tag)
    monkeypatch.chdir(root)
    return root


class TestDev0Baseline:
    """DEV0_STABLE: tries explicit baseline tag, falls back to previous release."""

    def test_uses_baseline_tag(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        _workspace_with_version(tmp_path, monkeypatch, "1.0.0.dev0", [
            "mylib/v1.0.0.dev0-base",
        ])
        with diny.provide():
            run_cli("status")
        # Baseline exists and matches HEAD, so no changes.
        assert "No changes detected" in capsys.readouterr().out

    def test_falls_back_to_previous_release(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        ws = _workspace_with_version(tmp_path, monkeypatch, "1.0.0.dev0", [
            "mylib/v0.9.0",
        ])
        # Edit a file so there's a diff from the previous release.
        (ws / "packages" / "mylib" / "mylib" / "__init__.py").write_text("# new")
        git(ws, "add", ".")
        git(ws, "commit", "-m", "change")
        with diny.provide():
            run_cli("status")
        assert "files changed" in capsys.readouterr().out


class TestDevKBaseline:
    """DEVK_STABLE: uses dev0 baseline tag as anchor for the cycle."""

    def test_uses_dev0_baseline(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        _workspace_with_version(tmp_path, monkeypatch, "1.0.0.dev3", [
            "mylib/v1.0.0.dev0-base",
        ])
        with diny.provide():
            run_cli("status")
        assert "No changes detected" in capsys.readouterr().out


class TestCleanBaseline:
    """CLEAN_STABLE/PRE: diffs against previous release."""

    def test_clean_stable_uses_previous_release(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        ws = _workspace_with_version(tmp_path, monkeypatch, "1.1.0", [
            "mylib/v1.0.0",
        ])
        (ws / "packages" / "mylib" / "mylib" / "__init__.py").write_text("# new")
        git(ws, "add", ".")
        git(ws, "commit", "-m", "change")
        with diny.provide():
            run_cli("status")
        assert "files changed" in capsys.readouterr().out

    def test_clean_pre_uses_previous_release(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        _workspace_with_version(tmp_path, monkeypatch, "1.0.0a1", [
            "mylib/v1.0.0a0",
        ])
        with diny.provide():
            run_cli("status")
        assert "No changes detected" in capsys.readouterr().out


class TestPostBaseline:
    """CLEAN_POST: diffs against the base stable release."""

    def test_post_diffs_against_stable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        ws = _workspace_with_version(tmp_path, monkeypatch, "1.0.0.post0", [
            "mylib/v1.0.0",
        ])
        (ws / "packages" / "mylib" / "mylib" / "__init__.py").write_text("# fix")
        git(ws, "add", ".")
        git(ws, "commit", "-m", "hotfix")
        with diny.provide():
            run_cli("status")
        assert "files changed" in capsys.readouterr().out

    def test_post_no_changes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        _workspace_with_version(tmp_path, monkeypatch, "1.0.0.post1", [
            "mylib/v1.0.0",
        ])
        with diny.provide():
            run_cli("status")
        assert "No changes detected" in capsys.readouterr().out


class TestNoBaseline:
    """No tags at all: initial release."""

    def test_no_tags_is_initial_release(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        _workspace_with_version(tmp_path, monkeypatch, "0.1.0.dev0", [])
        with diny.provide():
            run_cli("status")
        assert "initial release" in capsys.readouterr().out
