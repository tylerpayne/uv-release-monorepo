from __future__ import annotations

from pathlib import Path

import diny
import pytest

from conftest import run_cli


class TestClean:
    def test_removes_cache(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cache = workspace / ".uvr" / "cache"
        cache.mkdir(parents=True)
        (cache / "dummy").write_text("x")
        with diny.provide():
            run_cli("clean")
        assert not cache.exists()

    def test_nothing_to_clean(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli("clean")
        assert "Nothing to clean" in capsys.readouterr().out
