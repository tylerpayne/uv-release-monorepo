"""Tests for uv_release_monorepo.shared.utils.versions."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from uv_release_monorepo.shared.utils.versions import (
    bump_dev,
    bump_patch,
    find_previous_release,
    get_base_version,
    is_dev,
    make_dev,
    make_post,
    make_pre,
    parse_tag_version,
    parse_version,
    strip_dev,
    strip_version,
)


class TestParseVersion:
    def test_full_semver(self) -> None:
        v = parse_version("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_two_part_version(self) -> None:
        v = parse_version("1.2")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 0

    def test_single_part_version(self) -> None:
        v = parse_version("5")
        assert v.major == 5
        assert v.minor == 0
        assert v.patch == 0

    def test_zero_version(self) -> None:
        v = parse_version("0.0.0")
        assert v.major == 0
        assert v.minor == 0
        assert v.patch == 0

    def test_strips_dev(self) -> None:
        v = parse_version("1.2.3.dev0")
        assert v.patch == 3

    def test_strips_pre(self) -> None:
        v = parse_version("1.2.3a1")
        assert v.patch == 3

    def test_strips_post(self) -> None:
        v = parse_version("1.2.3.post0")
        assert v.patch == 3


class TestBumpPatch:
    def test_bump_full_version(self) -> None:
        assert bump_patch("1.2.3") == "1.2.4"

    def test_bump_two_part(self) -> None:
        assert bump_patch("1.2") == "1.2.1"

    def test_bump_single_part(self) -> None:
        assert bump_patch("1") == "1.0.1"

    def test_bump_zero(self) -> None:
        assert bump_patch("0.0.0") == "0.0.1"

    def test_bump_high_patch(self) -> None:
        assert bump_patch("1.0.99") == "1.0.100"

    def test_bump_strips_dev(self) -> None:
        assert bump_patch("1.2.3.dev0") == "1.2.4"

    def test_bump_strips_pre(self) -> None:
        assert bump_patch("1.2.3a1") == "1.2.4"


class TestStripDev:
    def test_strips_dev0(self) -> None:
        assert strip_dev("1.2.3.dev0") == "1.2.3"

    def test_strips_devN(self) -> None:
        assert strip_dev("1.2.3.dev5") == "1.2.3"

    def test_no_dev(self) -> None:
        assert strip_dev("1.2.3") == "1.2.3"

    def test_post_dev(self) -> None:
        assert strip_dev("1.2.3.post0.dev0") == "1.2.3.post0"


class TestMakeDev:
    def test_adds_dev0(self) -> None:
        assert make_dev("1.2.3") == "1.2.3.dev0"

    def test_idempotent(self) -> None:
        assert make_dev("1.2.3.dev0") == "1.2.3.dev0"

    def test_replaces_devN(self) -> None:
        assert make_dev("1.2.3.dev5") == "1.2.3.dev0"

    def test_post_version(self) -> None:
        assert make_dev("1.2.3.post0") == "1.2.3.post0.dev0"


class TestBumpDev:
    def test_bump_dev0(self) -> None:
        assert bump_dev("1.2.3.dev0") == "1.2.3.dev1"

    def test_bump_dev5(self) -> None:
        assert bump_dev("1.2.3.dev5") == "1.2.3.dev6"

    def test_no_dev_adds_dev0(self) -> None:
        assert bump_dev("1.2.3") == "1.2.3.dev0"


class TestClassifiers:
    def test_is_dev(self) -> None:
        assert is_dev("1.2.3.dev0") is True
        assert is_dev("1.2.3") is False
        assert is_dev("1.2.3a0") is False


class TestStripVersion:
    def test_dev_only(self) -> None:
        assert strip_version("1.2.3.dev0", dev=True) == "1.2.3"

    def test_pre_only(self) -> None:
        assert strip_version("1.2.3a1", pre=True) == "1.2.3"

    def test_post_only(self) -> None:
        assert strip_version("1.2.3.post0", post=True) == "1.2.3"

    def test_dev_and_pre(self) -> None:
        assert strip_version("1.2.3rc1.dev0", dev=True, pre=True) == "1.2.3"

    def test_dev_and_post(self) -> None:
        assert strip_version("1.2.3.post0.dev0", dev=True, post=True) == "1.2.3"

    def test_all(self) -> None:
        assert (
            strip_version("1.2.3.post0.dev0", dev=True, pre=True, post=True) == "1.2.3"
        )

    def test_no_flags_is_noop(self) -> None:
        assert strip_version("1.2.3rc1.dev0") == "1.2.3rc1.dev0"

    def test_dev_leaves_pre(self) -> None:
        assert strip_version("1.2.3rc1.dev0", dev=True) == "1.2.3rc1"

    def test_pre_alone_on_pre_dev_is_noop(self) -> None:
        # pre regex requires suffix at end; .dev0 blocks it — use dev=True too
        assert strip_version("1.2.3a1.dev0", pre=True) == "1.2.3a1.dev0"

    def test_pre_alone_on_bare_pre(self) -> None:
        assert strip_version("1.2.3a1", pre=True) == "1.2.3"


class TestGetBaseVersion:
    def test_plain(self) -> None:
        assert get_base_version("1.2.3") == "1.2.3"

    def test_dev(self) -> None:
        assert get_base_version("1.2.3.dev0") == "1.2.3"

    def test_pre(self) -> None:
        assert get_base_version("1.2.3a1") == "1.2.3"
        assert get_base_version("1.2.3b0") == "1.2.3"
        assert get_base_version("1.2.3rc2") == "1.2.3"

    def test_post(self) -> None:
        assert get_base_version("1.2.3.post0") == "1.2.3"

    def test_post_dev(self) -> None:
        assert get_base_version("1.2.3.post0.dev0") == "1.2.3"


class TestMakePre:
    def test_alpha(self) -> None:
        assert make_pre("1.2.3.dev2", "a") == "1.2.3a0"

    def test_beta(self) -> None:
        assert make_pre("1.2.3.dev0", "b", 1) == "1.2.3b1"

    def test_rc(self) -> None:
        assert make_pre("1.2.3.dev0", "rc", 2) == "1.2.3rc2"


class TestMakePost:
    def test_post0(self) -> None:
        assert make_post("1.2.3") == "1.2.3.post0"

    def test_post1(self) -> None:
        assert make_post("1.2.3", 1) == "1.2.3.post1"


class TestParseTagVersion:
    def test_simple_tag(self) -> None:
        assert parse_tag_version("pkg/v1.0.0") == "1.0.0"

    def test_dev_tag(self) -> None:
        assert parse_tag_version("my-pkg/v2.3.4.dev0") == "2.3.4.dev0"

    def test_hyphenated_name(self) -> None:
        assert parse_tag_version("my-long-pkg/v0.1.0") == "0.1.0"


class TestFindPreviousRelease:
    """Tests for find_previous_release() — inverse version bump."""

    @staticmethod
    def _repo(existing_tags: set[str]) -> MagicMock:
        """Create a mock repo with the given tags."""
        mock = MagicMock()
        mock.references.get.side_effect = lambda ref: (
            True if ref in {f"refs/tags/{t}" for t in existing_tags} else None
        )
        mock.listall_references.return_value = [f"refs/tags/{t}" for t in existing_tags]
        return mock

    # Case 1: dev N > 0 → previous dev
    def test_dev_n_gt_0(self) -> None:
        repo = self._repo({"pkg/v1.0.1.dev2"})
        assert find_previous_release("1.0.1.dev3", "pkg", repo) == "1.0.1.dev2"

    def test_dev_1_to_dev_0(self) -> None:
        repo = self._repo({"pkg/v1.0.1.dev0"})
        assert find_previous_release("1.0.1.dev1", "pkg", repo) == "1.0.1.dev0"

    # Case 2: pre N > 0 → decrement pre
    def test_alpha_n_gt_0(self) -> None:
        repo = self._repo({"pkg/v1.0.1a0"})
        assert find_previous_release("1.0.1a1.dev0", "pkg", repo) == "1.0.1a0"

    def test_beta_n_gt_0(self) -> None:
        repo = self._repo({"pkg/v1.0.1b1"})
        assert find_previous_release("1.0.1b2.dev0", "pkg", repo) == "1.0.1b1"

    def test_rc_n_gt_0(self) -> None:
        repo = self._repo({"pkg/v1.0.1rc2"})
        assert find_previous_release("1.0.1rc3.dev0", "pkg", repo) == "1.0.1rc2"

    # Case 3: post N > 0 → decrement post
    def test_post_n_gt_0(self) -> None:
        repo = self._repo({"pkg/v1.0.1.post0"})
        assert find_previous_release("1.0.1.post1.dev0", "pkg", repo) == "1.0.1.post0"

    def test_post_2_to_post_1(self) -> None:
        repo = self._repo({"pkg/v1.0.1.post1"})
        assert find_previous_release("1.0.1.post2.dev0", "pkg", repo) == "1.0.1.post1"

    # Case 4: pre 0 → previous final
    def test_alpha_0_to_previous_patch(self) -> None:
        repo = self._repo({"pkg/v1.0.0"})
        assert find_previous_release("1.0.1a0.dev0", "pkg", repo) == "1.0.0"

    def test_rc_0_to_previous_patch(self) -> None:
        repo = self._repo({"pkg/v2.1.3"})
        assert find_previous_release("2.1.4rc0.dev0", "pkg", repo) == "2.1.3"

    def test_alpha_0_minor_bump_globs(self) -> None:
        repo = self._repo({"pkg/v1.0.5"})
        assert find_previous_release("1.1.0a0.dev0", "pkg", repo) == "1.0.5"

    # Case 5: post 0 → the final it patches
    def test_post_0_to_final(self) -> None:
        repo = self._repo({"pkg/v1.0.1"})
        assert find_previous_release("1.0.1.post0.dev0", "pkg", repo) == "1.0.1"

    # Case 6: patch > 0 → decrement patch
    def test_patch_decrement(self) -> None:
        repo = self._repo({"pkg/v1.0.0"})
        assert find_previous_release("1.0.1.dev0", "pkg", repo) == "1.0.0"

    def test_patch_decrement_higher(self) -> None:
        repo = self._repo({"pkg/v1.0.4"})
        assert find_previous_release("1.0.5.dev0", "pkg", repo) == "1.0.4"

    # Case 7: minor > 0, patch == 0 → glob X.(Y-1).*
    def test_minor_bump_globs(self) -> None:
        repo = self._repo({"pkg/v1.0.3"})
        assert find_previous_release("1.1.0.dev0", "pkg", repo) == "1.0.3"

    def test_minor_bump_picks_highest(self) -> None:
        repo = self._repo({"pkg/v1.0.1", "pkg/v1.0.3", "pkg/v1.0.2"})
        assert find_previous_release("1.1.0.dev0", "pkg", repo) == "1.0.3"

    def test_minor_bump_ignores_base_tags(self) -> None:
        repo = self._repo({"pkg/v1.0.3", "pkg/v1.0.4.dev0-base"})
        assert find_previous_release("1.1.0.dev0", "pkg", repo) == "1.0.3"

    # Case 8: major > 0, minor == 0 → glob (X-1).*
    def test_major_bump_globs(self) -> None:
        repo = self._repo({"pkg/v0.9.5"})
        assert find_previous_release("1.0.0.dev0", "pkg", repo) == "0.9.5"

    def test_major_bump_picks_highest(self) -> None:
        repo = self._repo({"pkg/v0.1.0", "pkg/v0.9.5", "pkg/v0.8.0"})
        assert find_previous_release("1.0.0.dev0", "pkg", repo) == "0.9.5"

    def test_major_2_to_1(self) -> None:
        repo = self._repo({"pkg/v1.5.2"})
        assert find_previous_release("2.0.0.dev0", "pkg", repo) == "1.5.2"

    # Case 9: 0.0.0 → error
    def test_zero_version_raises(self) -> None:
        repo = self._repo(set())
        with pytest.raises(ValueError, match="0.0.0"):
            find_previous_release("0.0.0.dev0", "pkg", repo)

    # Edge cases
    def test_not_dev_version_returns_none(self) -> None:
        repo = self._repo(set())
        assert find_previous_release("1.0.0", "pkg", repo) is None

    def test_tag_not_found_falls_through(self) -> None:
        """If expected tag doesn't exist, try next rule."""
        # 1.0.1.dev0 expects 1.0.0 but it doesn't exist → returns None
        repo = self._repo(set())
        assert find_previous_release("1.0.1.dev0", "pkg", repo) is None

    def test_glob_returns_none_if_no_matches(self) -> None:
        repo = self._repo(set())
        assert find_previous_release("1.1.0.dev0", "pkg", repo) is None
