"""Tests for --rebuild specific packages in change detection."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from uv_release_monorepo.shared.models import PackageInfo
from uv_release_monorepo.shared.utils.changes import detect_changes

_MOD = "uv_release_monorepo.shared.utils.changes"


def _mock_repo() -> MagicMock:
    repo = MagicMock()
    repo.revparse_single.return_value = MagicMock()
    repo.references.get.return_value = None
    return repo


class TestRebuildSpecificPackages:
    """Tests for the rebuild parameter in detect_changes."""

    @pytest.fixture
    def packages(self) -> dict[str, PackageInfo]:
        return {
            "pkg-a": PackageInfo(path="packages/a", version="1.0.0.dev0", deps=[]),
            "pkg-b": PackageInfo(
                path="packages/b", version="1.0.0.dev0", deps=["pkg-a"]
            ),
            "pkg-c": PackageInfo(
                path="packages/c", version="1.0.0.dev0", deps=["pkg-b"]
            ),
        }

    @pytest.fixture
    def baselines(self) -> dict[str, str]:
        return {
            "pkg-a": "pkg-a/v1.0.0.dev0-base",
            "pkg-b": "pkg-b/v1.0.0.dev0-base",
            "pkg-c": "pkg-c/v1.0.0.dev0-base",
        }

    @patch(f"{_MOD}.path_changed", return_value=False)
    @patch(f"{_MOD}._resolve_tag", return_value=MagicMock())
    @patch(f"{_MOD}.print_step")
    def test_rebuild_single_package(
        self,
        _step: MagicMock,
        _resolve: MagicMock,
        _changed: MagicMock,
        packages: dict[str, PackageInfo],
        baselines: dict[str, str],
    ) -> None:
        """--rebuild pkg-a marks pkg-a and its dependents dirty."""
        changed = detect_changes(
            packages,
            baselines=baselines,
            rebuild_all=False,
            rebuild=["pkg-a"],
            repo=_mock_repo(),
        )
        assert set(changed) == {"pkg-a", "pkg-b", "pkg-c"}

    @patch(f"{_MOD}.path_changed", return_value=False)
    @patch(f"{_MOD}._resolve_tag", return_value=MagicMock())
    @patch(f"{_MOD}.print_step")
    def test_rebuild_leaf_no_propagation(
        self,
        _step: MagicMock,
        _resolve: MagicMock,
        _changed: MagicMock,
        packages: dict[str, PackageInfo],
        baselines: dict[str, str],
    ) -> None:
        """--rebuild pkg-c only marks pkg-c dirty (no dependents)."""
        changed = detect_changes(
            packages,
            baselines=baselines,
            rebuild_all=False,
            rebuild=["pkg-c"],
            repo=_mock_repo(),
        )
        assert set(changed) == {"pkg-c"}

    @patch(f"{_MOD}.path_changed")
    @patch(f"{_MOD}._resolve_tag", return_value=MagicMock())
    @patch(f"{_MOD}.print_step")
    def test_rebuild_combines_with_normal_detection(
        self,
        _step: MagicMock,
        _resolve: MagicMock,
        mock_changed: MagicMock,
        packages: dict[str, PackageInfo],
        baselines: dict[str, str],
    ) -> None:
        """--rebuild adds to normal change detection, not replaces it."""
        mock_changed.side_effect = lambda _r, _o, _n, p: p == "packages/c"

        changed = detect_changes(
            packages,
            baselines=baselines,
            rebuild_all=False,
            rebuild=["pkg-a"],
            repo=_mock_repo(),
        )
        # pkg-a from --rebuild, pkg-c from git changes, pkg-b from propagation
        assert set(changed) == {"pkg-a", "pkg-b", "pkg-c"}

    @patch(f"{_MOD}.path_changed", return_value=False)
    @patch(f"{_MOD}._resolve_tag", return_value=MagicMock())
    @patch(f"{_MOD}.print_step")
    def test_rebuild_unknown_package_exits(
        self,
        _step: MagicMock,
        _resolve: MagicMock,
        _changed: MagicMock,
        packages: dict[str, PackageInfo],
        baselines: dict[str, str],
    ) -> None:
        """--rebuild with unknown package name exits with error."""
        with pytest.raises(SystemExit):
            detect_changes(
                packages,
                baselines=baselines,
                rebuild_all=False,
                rebuild=["nonexistent"],
                repo=_mock_repo(),
            )
