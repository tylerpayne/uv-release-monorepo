"""Version parsing and bumping utilities.

Handles conversion between version strings and semver objects, with
special handling for incomplete version strings (e.g., "1.0" -> "1.0.0")
and PEP 440 dev/pre/post versions.
"""

from __future__ import annotations

import re

import semver

_DEV_RE = re.compile(r"\.dev\d*$")
_DEV_NUM_RE = re.compile(r"\.dev(\d+)$")


def strip_dev(version_str: str) -> str:
    """Remove a PEP 440 ``.devN`` suffix if present.

    Examples:
        "1.2.3.dev0" -> "1.2.3"
        "1.2.3" -> "1.2.3"
        "1.2.3.post0.dev0" -> "1.2.3.post0"
    """
    return _DEV_RE.sub("", version_str)


def make_dev(version_str: str) -> str:
    """Add a ``.dev0`` suffix. Idempotent.

    Examples:
        "1.2.3" -> "1.2.3.dev0"
        "1.2.3.dev0" -> "1.2.3.dev0"
        "1.2.3.post0" -> "1.2.3.post0.dev0"
    """
    return f"{strip_dev(version_str)}.dev0"


def bump_dev(version_str: str) -> str:
    """Increment the dev number.

    Examples:
        "1.2.3.dev0" -> "1.2.3.dev1"
        "1.2.3.dev5" -> "1.2.3.dev6"
        "1.2.3" -> "1.2.3.dev0"  (adds .dev0 if not present)
    """
    m = _DEV_NUM_RE.search(version_str)
    if m:
        n = int(m.group(1))
        return version_str[: m.start()] + f".dev{n + 1}"
    return f"{version_str}.dev0"


def is_dev(version_str: str) -> bool:
    """Check if a version has a .devN suffix."""
    return _DEV_RE.search(version_str) is not None


def strip_version(
    version_str: str,
    *,
    dev: bool = False,
    pre: bool = False,
    post: bool = False,
) -> str:
    """Selectively strip PEP 440 suffixes from a version string.

    Args:
        version_str: The version to strip.
        dev: Strip ``.devN`` suffix.
        pre: Strip ``aN``, ``bN``, ``rcN`` suffix.
        post: Strip ``.postN`` suffix.

    Suffixes are stripped in order: dev, post, pre (innermost-out).

    Examples:
        strip_version("1.2.3rc1.dev0", dev=True) -> "1.2.3rc1"
        strip_version("1.2.3rc1.dev0", dev=True, pre=True) -> "1.2.3"
        strip_version("1.2.3.post0.dev0", dev=True, post=True) -> "1.2.3"
        strip_version("1.2.3.post0.dev0", dev=True, pre=True, post=True) -> "1.2.3"
    """
    v = version_str
    if dev:
        v = _DEV_RE.sub("", v)
    if post:
        v = re.sub(r"\.post\d+$", "", v)
    if pre:
        v = re.sub(r"(a|b|rc)\d+$", "", v)
    return v


def get_base_version(version_str: str) -> str:
    """Strip all dev/pre/post suffixes to get the base X.Y.Z.

    Examples:
        "1.2.3.dev0" -> "1.2.3"
        "1.2.3a1" -> "1.2.3"
        "1.2.3.post0.dev0" -> "1.2.3"
        "1.2.3rc2" -> "1.2.3"
    """
    return strip_version(version_str, dev=True, pre=True, post=True)


def make_pre(version_str: str, kind: str, n: int = 0) -> str:
    """Create a pre-release version.

    Args:
        version_str: Base version (dev suffix stripped).
        kind: One of "a" (alpha), "b" (beta), "rc" (release candidate).
        n: Pre-release number (default 0).

    Examples:
        make_pre("1.2.3.dev2", "a") -> "1.2.3a0"
        make_pre("1.2.3.dev2", "rc", 1) -> "1.2.3rc1"
    """
    return f"{get_base_version(version_str)}{kind}{n}"


def make_post(version_str: str, n: int = 0) -> str:
    """Create a post-release version.

    Args:
        version_str: Must be a final release version.
        n: Post-release number (default 0).

    Examples:
        make_post("1.2.3") -> "1.2.3.post0"
        make_post("1.2.3", 1) -> "1.2.3.post1"
    """
    return f"{get_base_version(version_str)}.post{n}"


def find_previous_release(
    version_str: str,
    name: str,
    repo: object,
) -> str | None:
    """Derive the previous release version from a dev version string.

    Uses O(1) ref lookups for the common cases, falling back to a narrow
    glob only for minor/major bumps.

    Args:
        version_str: Current version (e.g. "1.0.1.dev0").
        name: Package name for tag prefix.
        repo: pygit2.Repository for ref lookups.

    Returns:
        The previous release version string, or None if no previous release.

    Raises:
        ValueError: If version is 0.0.0.dev0 (no possible previous release).

    Examples:
        "1.0.1.dev3"       → "1.0.1.dev2"
        "1.0.1.dev0"       → "1.0.0"
        "1.0.1a1.dev0"     → "1.0.1a0"
        "1.0.1a0.dev0"     → "1.0.0"
        "1.0.1.post1.dev0" → "1.0.1.post0"
        "1.0.1.post0.dev0" → "1.0.1"
        "1.1.0.dev0"       → glob pkg/v1.0.* → highest
        "2.0.0.dev0"       → glob pkg/v1.* → highest
    """

    def _tag_exists(ver: str) -> bool:
        return repo.references.get(f"refs/tags/{name}/v{ver}") is not None  # type: ignore[union-attr]

    def _glob_highest(prefix: str) -> str | None:
        """Find highest version matching a tag prefix via ref scan."""
        ref_prefix = f"refs/tags/{name}/v{prefix}"
        candidates = []
        for ref in repo.listall_references():  # type: ignore[union-attr]
            if ref.startswith(ref_prefix) and not ref.endswith("-base"):
                ver_str = ref.split("/v")[-1]
                try:
                    candidates.append((parse_version(ver_str), ver_str))
                except (ValueError, TypeError):
                    continue
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][1]

    # Extract dev number
    dev_m = _DEV_NUM_RE.search(version_str)
    if not dev_m:
        # Not a dev version — can't determine previous
        return None

    dev_n = int(dev_m.group(1))
    without_dev = strip_dev(version_str)

    # Case 1: dev N > 0 → previous dev
    if dev_n > 0:
        prev = f"{without_dev[: dev_m.start()]}.dev{dev_n - 1}"
        if _tag_exists(prev):
            return prev

    # Case 2: pre N > 0 → decrement pre
    pre_m = re.search(r"(a|b|rc)(\d+)$", without_dev)
    if pre_m:
        pre_n = int(pre_m.group(2))
        if pre_n > 0:
            prev = f"{without_dev[: pre_m.start()]}{pre_m.group(1)}{pre_n - 1}"
            if _tag_exists(prev):
                return prev
        # Case 4: pre 0 → previous final (strip pre, find last final)
        base = get_base_version(without_dev)
        sv = parse_version(base)
        if sv.patch > 0:
            prev = f"{sv.major}.{sv.minor}.{sv.patch - 1}"
            if _tag_exists(prev):
                return prev
        if sv.minor > 0:
            return _glob_highest(f"{sv.major}.{sv.minor - 1}.")
        if sv.major > 0:
            return _glob_highest(f"{sv.major - 1}.")
        return None

    # Case 3: post N > 0 → decrement post
    post_m = re.search(r"\.post(\d+)$", without_dev)
    if post_m:
        post_n = int(post_m.group(1))
        if post_n > 0:
            prev = f"{without_dev[: post_m.start()]}.post{post_n - 1}"
            if _tag_exists(prev):
                return prev
        # Case 5: post 0 → the final it patches
        prev = without_dev[: post_m.start()]
        if _tag_exists(prev):
            return prev
        return None

    # Plain X.Y.Z.dev0 — find previous final
    sv = parse_version(without_dev)

    # Case 6: patch > 0 → decrement patch
    if sv.patch > 0:
        prev = f"{sv.major}.{sv.minor}.{sv.patch - 1}"
        if _tag_exists(prev):
            return prev

    # Case 7: minor > 0 → glob X.(Y-1).*
    if sv.minor > 0:
        return _glob_highest(f"{sv.major}.{sv.minor - 1}.")

    # Case 8: major > 0 → glob (X-1).*
    if sv.major > 0:
        return _glob_highest(f"{sv.major - 1}.")

    # Case 9: 0.0.0 — no previous release possible
    msg = f"Cannot determine previous release for {version_str} — version is 0.0.0"
    raise ValueError(msg)


def parse_tag_version(tag: str) -> str:
    """Extract the version string from a release tag.

    Tags follow the pattern ``{package-name}/v{version}``.

    Examples:
        "pkg/v1.0.0" -> "1.0.0"
        "my-pkg/v2.3.4.dev0" -> "2.3.4.dev0"
    """
    return tag.split("/v")[-1]


def parse_version(version_str: str) -> semver.Version:
    """Parse a version string into a semver.Version object.

    Strips all dev/pre/post suffixes first, then handles incomplete versions
    by padding with zeros:
    - "1" -> "1.0.0"
    - "1.2" -> "1.2.0"
    - "1.2.3" -> "1.2.3"
    - "1.2.3.dev0" -> "1.2.3"
    - "1.2.3a1" -> "1.2.3"
    """
    cleaned = get_base_version(version_str)
    parts = cleaned.split(".")
    while len(parts) < 3:
        parts.append("0")
    return semver.Version.parse(".".join(parts[:3]))


def bump_patch(version_str: str) -> str:
    """Increment the patch version and return as a string.

    Strips all dev/pre/post suffixes before bumping.

    Examples:
        "1.2.3" -> "1.2.4"
        "1.2.3.dev0" -> "1.2.4"
        "1.2.3a1" -> "1.2.4"
        "1.0" -> "1.0.1"
    """
    return str(parse_version(version_str).bump_patch())
