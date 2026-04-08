"""Tests for tag conflict checking with skip awareness."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from uv_release_monorepo.shared.models import ChangedPackage, PackageInfo, PlanConfig
from uv_release_monorepo.shared.planner import ReleasePlanner

from tests._helpers import _make_ctx


def _changed_pkg(name: str, version: str = "1.0.0") -> ChangedPackage:
    return ChangedPackage(
        path=f"packages/{name}",
        version=version,
        deps=[],
        current_version=f"{version}.dev0",
        release_version=version,
        next_version=f"{version[:-1]}{int(version[-1]) + 1}.dev0",
        runners=[["ubuntu-latest"]],
    )


def _config(**overrides: object) -> PlanConfig:
    defaults = dict(
        rebuild_all=True,
        matrix={},
        uvr_version="0.1.0",
        dry_run=True,
    )
    defaults.update(overrides)  # type: ignore[arg-type]
    return PlanConfig(**defaults)  # type: ignore[arg-type]


class TestTagConflicts:
    """Tests for _find_tag_conflicts and _check_tag_conflicts."""

    def test_no_conflicts_when_tags_missing(self) -> None:
        """No conflicts when no tags exist."""
        packages = {"pkg-a": PackageInfo(path="a", version="1.0.0.dev0", deps=[])}
        ctx = _make_ctx(packages)
        planner = ReleasePlanner(_config(), ctx)
        changed = {"pkg-a": _changed_pkg("pkg-a")}

        conflicts = planner._find_tag_conflicts(changed)
        assert conflicts == []

    def test_release_tag_conflict_detected(self) -> None:
        """Detects conflict when release tag already exists."""
        packages = {"pkg-a": PackageInfo(path="a", version="1.0.0.dev0", deps=[])}
        ctx = _make_ctx(packages)
        # Make release tag exist
        ctx.repo.references.get.side_effect = lambda ref: (  # type: ignore[union-attr]
            MagicMock() if ref == "refs/tags/pkg-a/v1.0.0" else None
        )
        planner = ReleasePlanner(_config(), ctx)
        changed = {"pkg-a": _changed_pkg("pkg-a")}

        conflicts = planner._find_tag_conflicts(changed)
        assert "pkg-a/v1.0.0" in conflicts

    def test_release_tag_conflict_skipped_when_release_skipped(self) -> None:
        """No release tag conflict when uvr-release is in skip set."""
        packages = {"pkg-a": PackageInfo(path="a", version="1.0.0.dev0", deps=[])}
        ctx = _make_ctx(packages)
        # Make release tag exist
        ctx.repo.references.get.side_effect = lambda ref: (  # type: ignore[union-attr]
            MagicMock() if ref == "refs/tags/pkg-a/v1.0.0" else None
        )
        planner = ReleasePlanner(_config(skip={"uvr-release"}), ctx)
        changed = {"pkg-a": _changed_pkg("pkg-a")}

        conflicts = planner._find_tag_conflicts(changed)
        assert conflicts == []

    def test_baseline_tag_conflict_always_checked(self) -> None:
        """Baseline tag conflicts are always checked, even with release skipped."""
        packages = {"pkg-a": PackageInfo(path="a", version="1.0.0.dev0", deps=[])}
        ctx = _make_ctx(packages)
        changed = {"pkg-a": _changed_pkg("pkg-a")}
        base_tag = f"pkg-a/v{changed['pkg-a'].next_version}-base"
        ctx.repo.references.get.side_effect = lambda ref: (  # type: ignore[union-attr]
            MagicMock() if ref == f"refs/tags/{base_tag}" else None
        )
        planner = ReleasePlanner(_config(skip={"uvr-release"}), ctx)

        conflicts = planner._find_tag_conflicts(changed)
        assert base_tag in conflicts

    def test_check_tag_conflicts_aborts_on_conflict(self) -> None:
        """_check_tag_conflicts calls exit_fatal when conflicts exist."""
        packages = {"pkg-a": PackageInfo(path="a", version="1.0.0.dev0", deps=[])}
        ctx = _make_ctx(packages)
        ctx.repo.references.get.side_effect = lambda ref: (  # type: ignore[union-attr]
            MagicMock() if ref == "refs/tags/pkg-a/v1.0.0" else None
        )
        planner = ReleasePlanner(_config(), ctx)
        changed = {"pkg-a": _changed_pkg("pkg-a")}

        with pytest.raises(SystemExit):
            planner._check_tag_conflicts(changed)

    def test_check_tag_conflicts_passes_when_release_skipped(self) -> None:
        """_check_tag_conflicts does not abort when uvr-release is skipped."""
        packages = {"pkg-a": PackageInfo(path="a", version="1.0.0.dev0", deps=[])}
        ctx = _make_ctx(packages)
        ctx.repo.references.get.side_effect = lambda ref: (  # type: ignore[union-attr]
            MagicMock() if ref == "refs/tags/pkg-a/v1.0.0" else None
        )
        planner = ReleasePlanner(_config(skip={"uvr-release"}), ctx)
        changed = {"pkg-a": _changed_pkg("pkg-a")}

        # Should not raise
        planner._check_tag_conflicts(changed)
