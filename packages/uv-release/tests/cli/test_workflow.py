from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import diny
import pytest
import yaml

from conftest import run_cli


class TestWorkflowValidate:
    def test_missing_file(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (workspace / ".github" / "workflows" / "release.yml").unlink()
        with diny.provide():
            run_cli("workflow", "validate")
        # ui.error writes to stderr.
        assert "does not exist" in capsys.readouterr().err

    def test_has_all_required_jobs(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli("workflow", "validate")
        out = capsys.readouterr().out
        assert "missing" not in out.lower()

    def test_missing_required_jobs(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        wf = workspace / ".github" / "workflows" / "release.yml"
        wf.write_text(yaml.dump({"jobs": {"build": {}}}))
        with diny.provide():
            run_cli("workflow", "validate")
        out = capsys.readouterr().out
        assert "validate" in out and "missing" in out.lower()

    def test_custom_workflow_dir(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        custom = workspace / "ci"
        custom.mkdir()
        (custom / "release.yml").write_text(
            yaml.dump(
                {
                    "jobs": {
                        "validate": {},
                        "build": {},
                        "release": {},
                        "publish": {},
                        "bump": {},
                    }
                }
            )
        )
        with diny.provide():
            run_cli("workflow", "validate", "--workflow-dir", "ci")
        out = capsys.readouterr().out
        assert "missing" not in out.lower()


class TestWorkflowUpgrade:
    def test_scaffolds_workflow(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (workspace / ".github" / "workflows" / "release.yml").unlink()
        with diny.provide():
            run_cli("workflow", "install")
        out = capsys.readouterr().out
        assert "Write" in out or "workflow-upgrade" in out
        wf = workspace / ".github" / "workflows" / "release.yml"
        assert wf.exists()

    def test_print_template_with_existing_file(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # release.yml is scaffolded by the workspace fixture, so it exists.
        # --print-template must short-circuit even without --upgrade/--force.
        # The buggy provider previously raised "already exists..." breaking
        # the uvx fetch path.
        with diny.provide():
            run_cli("workflow", "install", "--print-template")
        out = capsys.readouterr().out
        # Bundled template is YAML and includes the release workflow name.
        assert "name:" in out

    def test_upgrade_falls_back_when_workflow_version_missing(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # release.yml is already scaffolded by the fixture and no
        # workflow-version is recorded, mimicking a user whose workflow
        # predates version tracking. Mock only the fetch subprocess
        # (uvx / uv pip install) — git operations must hit the real
        # repo so the dirty-check doesn't spuriously fail.
        _real_run = subprocess.run

        def _mock(args, **kwargs):
            head = args[0] if args else ""
            if head in {"uvx", "uv"}:
                return subprocess.CompletedProcess(args, 1, stderr="mocked")
            return _real_run(args, **kwargs)

        with patch("subprocess.run", side_effect=_mock):
            with pytest.raises(SystemExit):
                with diny.provide():
                    run_cli("workflow", "install", "--upgrade")

        out = capsys.readouterr().out
        assert "No workflow-version recorded" in out, (
            f"expected fallback warning, got:\n{out}"
        )
        assert "uv-release 0.32.0" in out, (
            f"expected 0.32.0 baseline in output, got:\n{out}"
        )

    def test_upgrade_respects_from_version_override(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _real_run = subprocess.run

        def _mock(args, **kwargs):
            head = args[0] if args else ""
            if head in {"uvx", "uv"}:
                return subprocess.CompletedProcess(args, 1, stderr="mocked")
            return _real_run(args, **kwargs)

        with patch("subprocess.run", side_effect=_mock):
            with pytest.raises(SystemExit):
                with diny.provide():
                    run_cli(
                        "workflow",
                        "install",
                        "--upgrade",
                        "--from-version",
                        "0.34.1",
                    )

        out = capsys.readouterr().out
        assert "No workflow-version recorded" not in out, (
            f"--from-version should suppress the fallback warning, got:\n{out}"
        )
        assert "uv-release 0.34.1" in out, (
            f"expected --from-version baseline in output, got:\n{out}"
        )
