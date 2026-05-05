from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import diny
import pytest
import tomlkit

from conftest import run_cli, tag_all


class TestStatus:
    def test_shows_packages_and_changes(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli("status")
        out = capsys.readouterr().out
        assert "pkg-a" in out and "pkg-b" in out
        assert "0.1.0.dev0" in out
        assert "initial release" in out

    def test_no_changes_after_tagging(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tag_all(workspace)
        with diny.provide():
            run_cli("status")
        out = capsys.readouterr().out
        assert "Nothing changed since last release" in out

    def test_respects_config_exclude(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Add pkg-b to [tool.uvr.config].exclude. Status should hide pkg-b
        # the same way build / release / version do — exclude is a workspace-
        # wide filter, not a per-command flag.
        pyproject_path = workspace / "pyproject.toml"
        doc = cast(Any, tomlkit.loads(pyproject_path.read_text()))
        doc["tool"]["uvr"]["config"]["exclude"] = ["pkg-b"]
        pyproject_path.write_text(tomlkit.dumps(doc))

        with diny.provide():
            run_cli("status")
        out = capsys.readouterr().out
        assert "pkg-a" in out
        assert "pkg-b" not in out

    def test_respects_config_include(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Symmetric to exclude: include acts as an allowlist, hiding any
        # package not explicitly listed.
        pyproject_path = workspace / "pyproject.toml"
        doc = cast(Any, tomlkit.loads(pyproject_path.read_text()))
        doc["tool"]["uvr"]["config"]["include"] = ["pkg-a"]
        pyproject_path.write_text(tomlkit.dumps(doc))

        with diny.provide():
            run_cli("status")
        out = capsys.readouterr().out
        assert "pkg-a" in out
        assert "pkg-b" not in out
