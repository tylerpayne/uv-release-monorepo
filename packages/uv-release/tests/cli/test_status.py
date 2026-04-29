from __future__ import annotations

from pathlib import Path

import diny
import pytest

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
        assert "No changes detected" in out
