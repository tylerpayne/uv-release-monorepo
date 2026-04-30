from __future__ import annotations

from pathlib import Path

import diny
import pytest

from conftest import git, run_cli, tag_all


class TestRelease:
    def test_dev_dry_run_shows_plan(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli("release", "--dry-run", "--where", "local", "--dev")
        out = capsys.readouterr().out
        assert "Pipeline" in out

    def test_nothing_changed(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tag_all(workspace)
        with diny.provide():
            run_cli("release", "--dry-run", "--where", "local", "--dev")
        assert "Nothing changed" in capsys.readouterr().out

    def test_missing_workflow_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Release fails if no workflow file exists."""
        import tomlkit

        root = tmp_path
        (root / "pyproject.toml").write_text(
            tomlkit.dumps(
                {
                    "tool": {
                        "uv": {"workspace": {"members": ["packages/*"]}},
                        "uvr": {"config": {"latest": "pkg-a"}},
                    },
                }
            )
        )
        pkg = root / "packages" / "pkg-a"
        pkg.mkdir(parents=True)
        (pkg / "pyproject.toml").write_text(
            tomlkit.dumps(
                {
                    "project": {"name": "pkg-a", "version": "0.1.0.dev0"},
                    "build-system": {
                        "requires": ["hatchling"],
                        "build-backend": "hatchling.build",
                    },
                }
            )
        )
        (pkg / "pkg_a").mkdir()
        (pkg / "pkg_a" / "__init__.py").write_text("")
        git(root, "init")
        git(root, "config", "user.name", "test")
        git(root, "config", "user.email", "test@test")
        git(root, "add", ".")
        git(root, "commit", "-m", "init")
        monkeypatch.chdir(root)

        with pytest.raises(SystemExit):
            with diny.provide():
                run_cli("release", "--dry-run", "--where", "local", "--dev")
        assert "Workflow file not found" in capsys.readouterr().err

    def test_stable_from_dev_triggers_version_fix(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            with diny.provide():
                run_cli("release", "--dry-run", "--where", "local")
        assert "Dev versions need to be stabilized" in capsys.readouterr().err

    def test_skip_build(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli(
                "release", "--dry-run", "--where", "local", "--dev", "--skip", "build"
            )
        out = capsys.readouterr().out
        assert "build" in out and "(skip)" in out

    def test_skip_to(self, workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
        with diny.provide():
            run_cli(
                "release",
                "--dry-run",
                "--where",
                "local",
                "--dev",
                "--skip-to",
                "publish",
            )
        out = capsys.readouterr().out
        lines = [line.strip() for line in out.splitlines()]
        build_line = next(line for line in lines if line.startswith("build:"))
        release_line = next(line for line in lines if line.startswith("release:"))
        assert "(skip)" in build_line
        assert "(skip)" in release_line

    def test_reuse_run_skips_build(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli(
                "release",
                "--dry-run",
                "--where",
                "local",
                "--dev",
                "--reuse-run",
                "99999",
            )
        out = capsys.readouterr().out
        lines = [line.strip() for line in out.splitlines()]
        build_line = next(line for line in lines if line.startswith("build:"))
        assert "(skip)" in build_line

    def test_reuse_releases_skips_release(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli(
                "release", "--dry-run", "--where", "local", "--dev", "--reuse-releases"
            )
        out = capsys.readouterr().out
        lines = [line.strip() for line in out.splitlines()]
        release_line = next(line for line in lines if line.startswith("release:"))
        assert "(skip)" in release_line

    def test_custom_release_notes(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli(
                "release",
                "--dry-run",
                "--where",
                "local",
                "--dev",
                "--release-notes",
                "pkg-a",
                "Custom notes here",
            )
        out = capsys.readouterr().out
        assert "Custom notes here" in out

    def test_release_notes_from_file(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        notes_file = workspace.parent / "notes.md"
        notes_file.write_text("Notes from a file")
        with diny.provide():
            run_cli(
                "release",
                "--dry-run",
                "--where",
                "local",
                "--dev",
                "--release-notes",
                "pkg-a",
                f"@{notes_file}",
            )
        out = capsys.readouterr().out
        assert "Notes from a file" in out

    def test_packages_flag(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli(
                "release",
                "--dry-run",
                "--where",
                "local",
                "--dev",
                "--packages",
                "pkg-a",
            )
        out = capsys.readouterr().out
        assert "Pipeline" in out
        assert "pkg-a" in out

    def test_all_packages(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tag_all(workspace)
        # Bump to next dev versions so release tags don't already exist.
        with diny.provide():
            run_cli("bump", "--dev", "--no-push", "--force")
        with diny.provide():
            run_cli(
                "release",
                "--dry-run",
                "--where",
                "local",
                "--dev",
                "--all-packages",
            )
        out = capsys.readouterr().out
        assert "Pipeline" in out
