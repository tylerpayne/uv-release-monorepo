from __future__ import annotations

from pathlib import Path

import diny
import pytest

from conftest import run_cli, tag_all


class TestBuild:
    def test_nothing_to_build_after_tagging(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tag_all(workspace)
        with diny.provide():
            run_cli("build")
        assert "Nothing to build" in capsys.readouterr().out

    def test_all_packages(self, workspace: Path, mock_builds: list[list[str]]) -> None:
        with diny.provide():
            run_cli("build", "--all-packages")
        built = {c[2] for c in mock_builds}
        assert "packages/pkg-a" in built
        assert "packages/pkg-b" in built

    def test_select_single_package(
        self, workspace: Path, mock_builds: list[list[str]]
    ) -> None:
        with diny.provide():
            run_cli("build", "--packages", "pkg-a")
        built = {c[2] for c in mock_builds}
        assert "packages/pkg-a" in built
        assert "packages/pkg-b" not in built

    def test_auto_detect_changes(
        self, workspace: Path, mock_builds: list[list[str]]
    ) -> None:
        """Without flags, builds all changed packages (both, since no tags)."""
        with diny.provide():
            run_cli("build")
        assert len(mock_builds) == 2
