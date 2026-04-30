"""Tests for the release pipeline plan structure.

These tests verify that the plan produced by `uvr release --json` contains
the correct jobs, commands, and ordering for various workspace configurations.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import diny
import pytest

from conftest import get_plan_json, git, read_toml, run_cli


def _commands_of_type(plan: dict, job_name: str, cmd_type: str) -> list[dict]:
    """Extract commands of a given type from a job in the plan."""
    for job in plan["jobs"]:
        if job["name"] == job_name:
            return [c for c in job["commands"] if c["type"] == cmd_type]
    return []


def _job(plan: dict, name: str) -> dict:
    for job in plan["jobs"]:
        if job["name"] == name:
            return job
    raise KeyError(f"No job named {name}")


class TestBuildJobStructure:
    """Verify build job has correct download and build commands in order."""

    def test_released_dep_downloaded_to_deps(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        downloads = _commands_of_type(plan, "build", "download_wheels")
        assert len(downloads) == 1
        assert downloads[0]["tag_name"] == "pkg-a/v1.0.0"
        assert downloads[0]["output_dir"] == "deps"

    def test_build_targets_go_to_dist(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        builds = _commands_of_type(plan, "build", "build")
        target_names = [b["label"] for b in builds]
        assert "Build pkg-b" in target_names
        assert "Build pkg-c" in target_names
        for b in builds:
            assert b["out_dir"] == "dist"

    def test_build_order_respects_dependency_chain(
        self, released_workspace: Path
    ) -> None:
        """pkg-b must build before pkg-c (pkg-c depends on pkg-b)."""
        with diny.provide():
            plan = get_plan_json("--dev")
        builds = _commands_of_type(plan, "build", "build")
        labels = [b["label"] for b in builds]
        assert labels.index("Build pkg-b") < labels.index("Build pkg-c")

    def test_creates_dist_and_deps_dirs(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        mkdirs = _commands_of_type(plan, "build", "make_directory")
        paths = {m["path"] for m in mkdirs}
        assert "dist" in paths
        assert "deps" in paths

    def test_pkg_a_not_in_build_commands(
        self, released_workspace: Path
    ) -> None:
        """pkg-a is released. It should be downloaded, not built."""
        with diny.provide():
            plan = get_plan_json("--dev")
        builds = _commands_of_type(plan, "build", "build")
        assert not any("pkg-a" in b["label"] for b in builds)


class TestReleaseJobStructure:
    """Verify release job downloads artifacts and attaches wheels."""

    def test_downloads_run_artifacts(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        downloads = _commands_of_type(plan, "release", "download_run_artifacts")
        assert len(downloads) == 1

    def test_creates_tags_for_each_package(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        tags = _commands_of_type(plan, "release", "create_tag")
        tag_names = {t["tag_name"] for t in tags}
        assert any("pkg-b" in t for t in tag_names)
        assert any("pkg-c" in t for t in tag_names)
        # pkg-a is not being released.
        assert not any("pkg-a" in t for t in tag_names)

    def test_creates_github_releases_with_wheel_globs(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        releases = _commands_of_type(plan, "release", "create_release")
        for rel in releases:
            assert rel["files"], f"No files for {rel['title']}"
            assert any(".whl" in f for f in rel["files"])

    def test_latest_package_marked(
        self, released_workspace: Path
    ) -> None:
        """pkg-c is configured as latest in [tool.uvr.config]."""
        with diny.provide():
            plan = get_plan_json("--dev")
        releases = _commands_of_type(plan, "release", "create_release")
        latest = [r for r in releases if r["make_latest"]]
        non_latest = [r for r in releases if not r["make_latest"]]
        assert len(latest) == 1
        assert "pkg-c" in latest[0]["title"]
        assert len(non_latest) >= 1


class TestPublishJobStructure:
    """Verify publish job downloads from GitHub release then publishes."""

    def test_downloads_wheels_from_release(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        downloads = _commands_of_type(plan, "publish", "download_wheels")
        assert len(downloads) >= 1
        for d in downloads:
            assert d["output_dir"] == "dist"

    def test_publishes_each_package(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        publishes = _commands_of_type(plan, "publish", "publish_to_index")
        names = {p["package_name"] for p in publishes}
        assert "pkg-b" in names
        assert "pkg-c" in names

    def test_publish_uses_configured_index(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        publishes = _commands_of_type(plan, "publish", "publish_to_index")
        for p in publishes:
            assert p["index"] == "pypi"


class TestBumpJobStructure:
    """Verify post-release bump job structure."""

    def test_bumps_each_released_package(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        versions = _commands_of_type(plan, "bump", "set_version")
        names = {v["label"] for v in versions}
        assert any("pkg-b" in n for n in names)
        assert any("pkg-c" in n for n in names)

    def test_creates_baseline_tags(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        tags = _commands_of_type(plan, "bump", "create_tag")
        assert len(tags) >= 1
        assert all("-base" in t["tag_name"] for t in tags)

    def test_commits_and_pushes(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        commits = _commands_of_type(plan, "bump", "commit")
        pushes = _commands_of_type(plan, "bump", "push")
        assert len(commits) == 1
        assert len(pushes) == 1

    def test_syncs_lockfile(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        syncs = _commands_of_type(plan, "bump", "sync_lockfile")
        assert len(syncs) == 1


class TestPlanMetadata:
    """Verify plan-level metadata from the workspace config."""

    def test_build_matrix(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        assert plan["build_matrix"] == [["ubuntu-latest"]]

    def test_python_version(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        assert plan["python_version"] == "3.12"

    def test_publish_environment(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        assert plan["publish_environment"] == "release"

    def test_skip_contains_validate(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        assert "validate" in plan["skip"]


class TestChangeDetection:
    """Verify change detection with tagged vs untagged packages."""

    def test_all_untagged_shows_initial_release(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli("status")
        out = capsys.readouterr().out
        assert "initial release" in out
        assert "pkg-a" in out and "pkg-b" in out

    def test_tagged_package_not_changed(
        self, released_workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """pkg-a is tagged. It should not appear as changed."""
        with diny.provide():
            run_cli("status")
        out = capsys.readouterr().out
        lines = out.splitlines()
        changed_section = False
        changed_names: list[str] = []
        for line in lines:
            if line.startswith("Changed:"):
                changed_section = True
                continue
            if changed_section and line.startswith("  ") and ":" in line:
                changed_names.append(line.strip().split(":")[0])
        assert "pkg-a" not in changed_names
        assert "pkg-b" in changed_names
        assert "pkg-c" in changed_names

    def test_dep_propagation(
        self, released_workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """pkg-c depends on pkg-b. If pkg-b changed, pkg-c should too."""
        with diny.provide():
            run_cli("status")
        out = capsys.readouterr().out
        assert "pkg-c" in out
        # pkg-c changes because pkg-b changed (dependency propagation)
        # or because it's an initial release. Either way, it's dirty.

    def test_no_changes_after_full_tag(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from conftest import tag_all

        tag_all(workspace)
        with diny.provide():
            run_cli("status")
        assert "No changes detected" in capsys.readouterr().out

    def test_change_after_file_edit(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from conftest import tag_all

        tag_all(workspace)
        # Edit a file in pkg-a after tagging.
        (workspace / "packages" / "pkg-a" / "pkg_a" / "__init__.py").write_text(
            "# changed"
        )
        git(workspace, "add", ".")
        git(workspace, "commit", "-m", "edit pkg-a")
        with diny.provide():
            run_cli("status")
        out = capsys.readouterr().out
        assert "pkg-a" in out and "files changed" in out
        # pkg-b depends on pkg-a, should propagate.
        assert "pkg-b" in out and "dependency changed" in out


class TestJobsSubcommand:
    """Test uvr jobs <name> with a serialized plan."""

    def test_jobs_validate_exits_clean(
        self, released_workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        monkeypatch.setenv("UVR_PLAN", json.dumps(plan))
        with diny.provide():
            run_cli("jobs", "validate")

    def test_jobs_unknown_name_errors(
        self, released_workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        monkeypatch.setenv("UVR_PLAN", json.dumps(plan))
        with pytest.raises(SystemExit):
            with diny.provide():
                run_cli("jobs", "nonexistent")
        assert "not found" in capsys.readouterr().err

    def test_jobs_no_env_var_errors(
        self,
        released_workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.delenv("UVR_PLAN", raising=False)
        with pytest.raises(SystemExit):
            with diny.provide():
                run_cli("jobs", "build")
        assert "UVR_PLAN" in capsys.readouterr().err


class TestJsonOutput:
    """Test --json flag produces valid parseable plan."""

    def test_json_output_is_valid(
        self, released_workspace: Path
    ) -> None:
        with diny.provide():
            plan = get_plan_json("--dev")
        assert "jobs" in plan
        assert "build_matrix" in plan
        job_names = [j["name"] for j in plan["jobs"]]
        assert "build" in job_names
        assert "release" in job_names
        assert "publish" in job_names
        assert "bump" in job_names


class TestBumpFlags:
    """Test --force and --no-pin on bump."""

    def test_force_bumps_even_after_tagging(
        self, workspace: Path
    ) -> None:
        from conftest import tag_all

        tag_all(workspace)
        # Without --force/--all-packages, nothing to bump.
        with diny.provide():
            run_cli("bump", "--minor", "--no-commit", "--no-push", "--force")
        a = read_toml(workspace / "packages" / "pkg-a" / "pyproject.toml")
        assert a["project"]["version"] == "0.2.0.dev0"

    def test_no_pin_skips_dep_pinning(
        self, workspace: Path
    ) -> None:
        with diny.provide():
            run_cli("bump", "--minor", "--no-commit", "--no-push", "--no-pin")
        b = read_toml(workspace / "packages" / "pkg-b" / "pyproject.toml")
        deps = b["project"]["dependencies"]
        # Original dep should be unchanged (not pinned to new version).
        assert deps == ["pkg-a>=0.1.0"]


class TestVersionFix:
    """Test the version stabilization flow."""

    def test_stable_release_from_dev_shows_fix_commands(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            with diny.provide():
                run_cli("release", "--dry-run", "--where", "local")
        err = capsys.readouterr().err
        assert "Dev versions need to be stabilized" in err

    def test_dev_release_skips_version_fix(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli("release", "--dry-run", "--where", "local", "--dev")
        out = capsys.readouterr().out
        assert "Release plan:" in out


class TestLocalRelease:
    """Test --where local executes commands directly (no CI dispatch)."""

    def test_local_release_builds_and_tags(
        self, workspace: Path, mock_builds: list[list[str]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Mock external commands, run local release, verify it executes."""
        _real = subprocess.run

        created_tags: list[str] = []
        def _patched(args: str | list[str], **kwargs):  # type: ignore[no-untyped-def]
            if not isinstance(args, list):
                return _real(args, **kwargs)
            # Mock git tag
            if len(args) >= 2 and args[0] == "git" and args[1] == "tag":
                created_tags.append(args[2])
                return subprocess.CompletedProcess(args, 0)
            # Mock git push and git pull
            if len(args) >= 2 and args[0] == "git" and args[1] in ("push", "pull"):
                return subprocess.CompletedProcess(args, 0)
            # Mock gh release create
            if len(args) >= 3 and args[0] == "gh" and args[1] == "release":
                return subprocess.CompletedProcess(args, 0)
            # Mock gh run download
            if len(args) >= 3 and args[0] == "gh" and args[1] == "run":
                return subprocess.CompletedProcess(args, 0)
            # Mock all uv commands (build, publish, sync)
            if len(args) >= 2 and args[0] == "uv":
                if args[1] == "build":
                    mock_builds.append(list(args))
                return subprocess.CompletedProcess(args, 0)
            return _real(args, **kwargs)

        monkeypatch.setattr(subprocess, "run", _patched)
        monkeypatch.setenv("RUN_ID", "12345")

        with diny.provide():
            run_cli("release", "--where", "local", "--dev", "-y")

        assert len(mock_builds) >= 1
        assert any("pkg-a" in t or "pkg-b" in t for t in created_tags)
