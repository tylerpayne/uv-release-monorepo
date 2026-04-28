"""Tests for ReleaseTags.parse with fake GitRepo."""

from __future__ import annotations

from uv_release.states.release_tags import parse_release_tags

from ..conftest import FakeGitRepo, make_package, make_workspace


class TestNonDevPackage:
    """Non-dev packages look for an exact version match tag."""

    def test_with_matching_tag(self) -> None:
        pkg = make_package("a", version="1.0.0")
        ws = make_workspace({"a": pkg})
        repo = FakeGitRepo(tags={"a/v1.0.0": "sha1"})

        result = parse_release_tags(workspace=ws, git_repo=repo)

        assert result.tags == {"a": "a/v1.0.0"}

    def test_without_matching_tag(self) -> None:
        pkg = make_package("a", version="1.0.0")
        ws = make_workspace({"a": pkg})
        repo = FakeGitRepo(tags={})

        result = parse_release_tags(workspace=ws, git_repo=repo)

        assert result.tags == {}


class TestDevPackage:
    """Dev packages search for the latest past release tag."""

    def test_finds_latest_release(self) -> None:
        pkg = make_package("a", version="1.1.0.dev0")
        ws = make_workspace({"a": pkg})
        repo = FakeGitRepo(tags={"a/v1.0.0": "sha1"})

        result = parse_release_tags(workspace=ws, git_repo=repo)

        assert result.tags == {"a": "a/v1.0.0"}

    def test_no_past_release(self) -> None:
        pkg = make_package("a", version="1.0.0.dev0")
        ws = make_workspace({"a": pkg})
        repo = FakeGitRepo(tags={})

        result = parse_release_tags(workspace=ws, git_repo=repo)

        assert result.tags == {}

    def test_picks_highest_version(self) -> None:
        pkg = make_package("a", version="2.0.0.dev0")
        ws = make_workspace({"a": pkg})
        repo = FakeGitRepo(
            tags={
                "a/v1.0.0": "sha1",
                "a/v1.2.0": "sha2",
                "a/v1.1.0": "sha3",
            }
        )

        result = parse_release_tags(workspace=ws, git_repo=repo)

        assert result.tags == {"a": "a/v1.2.0"}

    def test_ignores_baseline_tags(self) -> None:
        pkg = make_package("a", version="1.1.0.dev0")
        ws = make_workspace({"a": pkg})
        repo = FakeGitRepo(
            tags={
                "a/v1.0.0": "sha1",
                "a/v1.0.0-base": "sha2",
            }
        )

        result = parse_release_tags(workspace=ws, git_repo=repo)

        assert result.tags == {"a": "a/v1.0.0"}

    def test_ignores_dev_release_tags(self) -> None:
        pkg = make_package("a", version="1.1.0.dev0")
        ws = make_workspace({"a": pkg})
        repo = FakeGitRepo(
            tags={
                "a/v1.0.0.dev1": "sha1",
                "a/v0.9.0": "sha2",
            }
        )

        result = parse_release_tags(workspace=ws, git_repo=repo)

        assert result.tags == {"a": "a/v0.9.0"}
