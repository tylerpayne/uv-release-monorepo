"""Tests for the ``uvr workflow config`` command."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from uv_release_monorepo.shared.utils.config import get_config
from uv_release_monorepo.shared.utils.toml import read_pyproject
from uv_release_monorepo.cli.workflow.config import cmd_config

from tests._helpers import _write_workspace_repo


def _config_args(**kwargs: object) -> argparse.Namespace:
    defaults: dict[str, object] = dict(
        editor=None,
        latest=None,
        include_packages=None,
        exclude_packages=None,
        remove_packages=None,
        clear=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdConfig:
    """Tests for cmd_config()."""

    def test_show_empty(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No config shows 'No workspace config set'."""
        _write_workspace_repo(tmp_path, ["pkg-alpha"])
        monkeypatch.chdir(tmp_path)

        cmd_config(_config_args())
        output = capsys.readouterr().out
        assert "No workspace config set" in output

    def test_set_editor(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sets the editor."""
        _write_workspace_repo(tmp_path, ["pkg-alpha"])
        monkeypatch.chdir(tmp_path)

        cmd_config(_config_args(editor="code"))

        doc = read_pyproject(tmp_path / "pyproject.toml")
        config = get_config(doc)
        assert config["editor"] == "code"

    def test_set_latest(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sets the latest package."""
        _write_workspace_repo(tmp_path, ["pkg-alpha"])
        monkeypatch.chdir(tmp_path)

        cmd_config(_config_args(latest="pkg-alpha"))

        doc = read_pyproject(tmp_path / "pyproject.toml")
        config = get_config(doc)
        assert config["latest"] == "pkg-alpha"

    def test_include_packages(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Adds packages to the include list."""
        _write_workspace_repo(tmp_path, ["pkg-alpha", "pkg-beta"])
        monkeypatch.chdir(tmp_path)

        cmd_config(_config_args(include_packages=["pkg-alpha", "pkg-beta"]))

        doc = read_pyproject(tmp_path / "pyproject.toml")
        config = get_config(doc)
        assert config["include"] == ["pkg-alpha", "pkg-beta"]

    def test_exclude_packages(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Adds packages to the exclude list."""
        _write_workspace_repo(tmp_path, ["pkg-alpha"])
        monkeypatch.chdir(tmp_path)

        cmd_config(_config_args(exclude_packages=["pkg-alpha"]))

        doc = read_pyproject(tmp_path / "pyproject.toml")
        config = get_config(doc)
        assert config["exclude"] == ["pkg-alpha"]

    def test_clear(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Clear removes all config."""
        _write_workspace_repo(tmp_path, ["pkg-alpha"])
        monkeypatch.chdir(tmp_path)

        # Set something first
        cmd_config(_config_args(editor="vim", latest="pkg-alpha"))
        # Then clear
        cmd_config(_config_args(clear=True))

        doc = read_pyproject(tmp_path / "pyproject.toml")
        config = get_config(doc)
        assert config["editor"] == ""
        assert config["latest"] == ""
        assert config["include"] == []
        assert config["exclude"] == []

    def test_remove_from_include(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Remove packages from the include list."""
        _write_workspace_repo(tmp_path, ["pkg-alpha", "pkg-beta"])
        monkeypatch.chdir(tmp_path)

        cmd_config(_config_args(include_packages=["pkg-alpha", "pkg-beta"]))
        cmd_config(
            _config_args(include_packages=["pkg-alpha"], remove_packages=["pkg-beta"])
        )

        doc = read_pyproject(tmp_path / "pyproject.toml")
        config = get_config(doc)
        assert config["include"] == ["pkg-alpha"]
