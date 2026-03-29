"""Tests for change detection utilities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from uv_release_monorepo.shared.models import PackageInfo
from uv_release_monorepo.shared.utils.changes import detect_changes


class TestDetectChanges:
    """Tests for detect_changes()."""

    @pytest.fixture
    def sample_packages(self) -> dict[str, PackageInfo]:
        """Create a sample package set for testing."""
        return {
            "pkg-a": PackageInfo(path="packages/a", version="1.0.0", deps=[]),
            "pkg-b": PackageInfo(path="packages/b", version="1.0.0", deps=["pkg-a"]),
            "pkg-c": PackageInfo(path="packages/c", version="1.0.0", deps=["pkg-b"]),
        }

    @pytest.fixture
    def all_tags(self) -> dict[str, str | None]:
        """All packages have a tag."""
        return {
            "pkg-a": "pkg-a/v1.0.0",
            "pkg-b": "pkg-b/v1.0.0",
            "pkg-c": "pkg-c/v1.0.0",
        }

    @pytest.fixture
    def no_tags(self) -> dict[str, str | None]:
        """No packages have tags (first release)."""
        return {"pkg-a": None, "pkg-b": None, "pkg-c": None}

    @patch("uv_release_monorepo.shared.utils.changes.diff_files")
    @patch("uv_release_monorepo.shared.utils.changes.print_step")
    def test_first_release_all_changed(
        self,
        mock_step: MagicMock,
        mock_diff: MagicMock,
        sample_packages: dict[str, PackageInfo],
        no_tags: dict[str, None],
    ) -> None:
        """On first release (no tags), all packages are marked changed."""
        changed = detect_changes(sample_packages, baselines=no_tags, rebuild_all=False)

        assert set(changed) == {"pkg-a", "pkg-b", "pkg-c"}

    @patch("uv_release_monorepo.shared.utils.changes.diff_files")
    @patch("uv_release_monorepo.shared.utils.changes.print_step")
    def test_rebuild_all_marks_everything_dirty(
        self,
        mock_step: MagicMock,
        mock_diff: MagicMock,
        sample_packages: dict[str, PackageInfo],
        all_tags: dict[str, str],
    ) -> None:
        """rebuild_all=True marks all packages as changed regardless of git diff."""
        changed = detect_changes(sample_packages, baselines=all_tags, rebuild_all=True)

        assert set(changed) == {"pkg-a", "pkg-b", "pkg-c"}

    @patch("uv_release_monorepo.shared.utils.changes.diff_files")
    @patch("uv_release_monorepo.shared.utils.changes.print_step")
    def test_single_package_changed(
        self,
        mock_step: MagicMock,
        mock_diff: MagicMock,
        sample_packages: dict[str, PackageInfo],
        all_tags: dict[str, str],
    ) -> None:
        """When only one leaf package changes, only it is rebuilt."""
        responses: dict[str, set[str]] = {
            "pkg-a/v1.0.0": set(),
            "pkg-b/v1.0.0": set(),
            "pkg-c/v1.0.0": {"packages/c/src.py"},
        }
        mock_diff.side_effect = lambda _repo, tag: responses.get(tag, set())

        changed = detect_changes(sample_packages, baselines=all_tags, rebuild_all=False)

        assert set(changed) == {"pkg-c"}

    @patch("uv_release_monorepo.shared.utils.changes.diff_files")
    @patch("uv_release_monorepo.shared.utils.changes.print_step")
    def test_dependency_change_propagates(
        self,
        mock_step: MagicMock,
        mock_diff: MagicMock,
        sample_packages: dict[str, PackageInfo],
        all_tags: dict[str, str],
    ) -> None:
        """When a dependency changes, its dependents are also marked dirty."""
        responses: dict[str, set[str]] = {
            "pkg-a/v1.0.0": {"packages/a/src.py"},
            "pkg-b/v1.0.0": set(),
            "pkg-c/v1.0.0": set(),
        }
        mock_diff.side_effect = lambda _repo, tag: responses.get(tag, set())

        changed = detect_changes(sample_packages, baselines=all_tags, rebuild_all=False)

        assert set(changed) == {"pkg-a", "pkg-b", "pkg-c"}

    @patch("uv_release_monorepo.shared.utils.changes.diff_files")
    @patch("uv_release_monorepo.shared.utils.changes.print_step")
    def test_middle_package_change_propagates_to_dependents(
        self,
        mock_step: MagicMock,
        mock_diff: MagicMock,
        sample_packages: dict[str, PackageInfo],
        all_tags: dict[str, str],
    ) -> None:
        """When a middle package changes, only it and its dependents are dirty."""
        responses: dict[str, set[str]] = {
            "pkg-a/v1.0.0": set(),
            "pkg-b/v1.0.0": {"packages/b/src.py"},
            "pkg-c/v1.0.0": set(),
        }
        mock_diff.side_effect = lambda _repo, tag: responses.get(tag, set())

        changed = detect_changes(sample_packages, baselines=all_tags, rebuild_all=False)

        assert set(changed) == {"pkg-b", "pkg-c"}

    @patch("uv_release_monorepo.shared.utils.changes.diff_files")
    @patch("uv_release_monorepo.shared.utils.changes.print_step")
    def test_root_pyproject_change_does_not_mark_packages_dirty(
        self,
        mock_step: MagicMock,
        mock_diff: MagicMock,
        sample_packages: dict[str, PackageInfo],
        all_tags: dict[str, str],
    ) -> None:
        """Root pyproject.toml changes alone don't trigger package rebuilds."""
        mock_diff.return_value = {"pyproject.toml"}

        changed = detect_changes(sample_packages, baselines=all_tags, rebuild_all=False)

        assert changed == []

    @patch("uv_release_monorepo.shared.utils.changes.diff_files")
    @patch("uv_release_monorepo.shared.utils.changes.print_step")
    def test_no_changes_returns_empty(
        self,
        mock_step: MagicMock,
        mock_diff: MagicMock,
        sample_packages: dict[str, PackageInfo],
        all_tags: dict[str, str],
    ) -> None:
        """When nothing changed, returns empty changed list."""
        mock_diff.return_value = {"unrelated/file.txt"}

        changed = detect_changes(sample_packages, baselines=all_tags, rebuild_all=False)

        assert changed == []


class TestDetectChangesDiamondDeps:
    """Test detect_changes with diamond dependency pattern."""

    @pytest.fixture
    def diamond_packages(self) -> dict[str, PackageInfo]:
        """Diamond: top depends on left and right, both depend on bottom."""
        return {
            "bottom": PackageInfo(path="packages/bottom", version="1.0.0", deps=[]),
            "left": PackageInfo(path="packages/left", version="1.0.0", deps=["bottom"]),
            "right": PackageInfo(
                path="packages/right", version="1.0.0", deps=["bottom"]
            ),
            "top": PackageInfo(
                path="packages/top", version="1.0.0", deps=["left", "right"]
            ),
        }

    @pytest.fixture
    def diamond_tags(self) -> dict[str, str | None]:
        """All diamond packages have tags."""
        return {
            "bottom": "bottom/v1.0.0",
            "left": "left/v1.0.0",
            "right": "right/v1.0.0",
            "top": "top/v1.0.0",
        }

    @patch("uv_release_monorepo.shared.utils.changes.diff_files")
    @patch("uv_release_monorepo.shared.utils.changes.print_step")
    def test_bottom_change_propagates_to_all(
        self,
        mock_step: MagicMock,
        mock_diff: MagicMock,
        diamond_packages: dict[str, PackageInfo],
        diamond_tags: dict[str, str],
    ) -> None:
        """Changing bottom affects all packages in diamond."""
        responses: dict[str, set[str]] = {
            "bottom/v1.0.0": {"packages/bottom/src.py"},
            "left/v1.0.0": set(),
            "right/v1.0.0": set(),
            "top/v1.0.0": set(),
        }
        mock_diff.side_effect = lambda _repo, tag: responses.get(tag, set())

        changed = detect_changes(
            diamond_packages, baselines=diamond_tags, rebuild_all=False
        )

        assert set(changed) == {"bottom", "left", "right", "top"}

    @patch("uv_release_monorepo.shared.utils.changes.diff_files")
    @patch("uv_release_monorepo.shared.utils.changes.print_step")
    def test_left_change_propagates_to_top_only(
        self,
        mock_step: MagicMock,
        mock_diff: MagicMock,
        diamond_packages: dict[str, PackageInfo],
        diamond_tags: dict[str, str],
    ) -> None:
        """Changing left affects only left and top."""
        responses: dict[str, set[str]] = {
            "bottom/v1.0.0": set(),
            "left/v1.0.0": {"packages/left/src.py"},
            "right/v1.0.0": set(),
            "top/v1.0.0": set(),
        }
        mock_diff.side_effect = lambda _repo, tag: responses.get(tag, set())

        changed = detect_changes(
            diamond_packages, baselines=diamond_tags, rebuild_all=False
        )

        assert set(changed) == {"left", "top"}

    @patch("uv_release_monorepo.shared.utils.changes.diff_files")
    @patch("uv_release_monorepo.shared.utils.changes.print_step")
    def test_top_change_only_affects_top(
        self,
        mock_step: MagicMock,
        mock_diff: MagicMock,
        diamond_packages: dict[str, PackageInfo],
        diamond_tags: dict[str, str],
    ) -> None:
        """Changing top affects only top (no dependents)."""
        responses: dict[str, set[str]] = {
            "bottom/v1.0.0": set(),
            "left/v1.0.0": set(),
            "right/v1.0.0": set(),
            "top/v1.0.0": {"packages/top/src.py"},
        }
        mock_diff.side_effect = lambda _repo, tag: responses.get(tag, set())

        changed = detect_changes(
            diamond_packages, baselines=diamond_tags, rebuild_all=False
        )

        assert set(changed) == {"top"}
