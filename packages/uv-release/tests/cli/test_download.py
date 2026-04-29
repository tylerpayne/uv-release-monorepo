from __future__ import annotations

from pathlib import Path

import diny
import pytest

from conftest import run_cli


class TestDownload:
    def test_no_args_errors(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            with diny.provide():
                run_cli("download")
        assert "Specify a package" in capsys.readouterr().err

    def test_no_remote_errors(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            with diny.provide():
                run_cli("download", "pkg-a")
        assert "Could not determine GitHub repo" in capsys.readouterr().err

    def test_run_id_no_remote_errors(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            with diny.provide():
                run_cli("download", "--run-id", "12345")
        assert "Could not determine GitHub repo" in capsys.readouterr().err
