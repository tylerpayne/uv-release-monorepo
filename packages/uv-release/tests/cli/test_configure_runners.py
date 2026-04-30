from __future__ import annotations

from pathlib import Path

import diny
import pytest

from conftest import read_toml, run_cli


class TestConfigureRunners:
    def test_show_mode_default(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli("configure", "runners")
        assert "Default: ubuntu-latest" in capsys.readouterr().out

    def test_add_runner(self, workspace: Path) -> None:
        with diny.provide():
            run_cli(
                "configure",
                "runners",
                "--package",
                "pkg-a",
                "--add",
                "self-hosted, linux",
            )
        runners = read_toml(workspace / "pyproject.toml")["tool"]["uvr"]["runners"]
        assert ["self-hosted", "linux"] in runners["pkg-a"]

    def test_add_strips_brackets(self, workspace: Path) -> None:
        with diny.provide():
            run_cli("configure", "runners", "--package", "pkg-a", "--add", "[macos-14]")
        runners = read_toml(workspace / "pyproject.toml")["tool"]["uvr"]["runners"]
        assert ["macos-14"] in runners["pkg-a"]

    def test_remove_runner(self, workspace: Path) -> None:
        with diny.provide():
            run_cli(
                "configure", "runners", "--package", "pkg-a", "--add", "ubuntu-latest"
            )
        with diny.provide():
            run_cli(
                "configure",
                "runners",
                "--package",
                "pkg-a",
                "--remove",
                "ubuntu-latest",
            )
        runners = read_toml(workspace / "pyproject.toml")["tool"]["uvr"]["runners"]
        assert "pkg-a" not in runners

    def test_clear_package(self, workspace: Path) -> None:
        with diny.provide():
            run_cli(
                "configure", "runners", "--package", "pkg-a", "--add", "ubuntu-latest"
            )
        with diny.provide():
            run_cli("configure", "runners", "--package", "pkg-a", "--clear")
        runners = read_toml(workspace / "pyproject.toml")["tool"]["uvr"]["runners"]
        assert "pkg-a" not in runners

    def test_clear_all(self, workspace: Path) -> None:
        with diny.provide():
            run_cli(
                "configure", "runners", "--package", "pkg-a", "--add", "ubuntu-latest"
            )
        with diny.provide():
            run_cli("configure", "runners", "--clear")
        runners = read_toml(workspace / "pyproject.toml")["tool"]["uvr"]["runners"]
        assert runners == {} or not runners

    def test_no_package_with_add_errors(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            with diny.provide():
                run_cli("configure", "runners", "--add", "ubuntu-latest")
        assert "Specify --package" in capsys.readouterr().err
