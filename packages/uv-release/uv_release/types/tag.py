"""Git tags tied to package versions."""

from __future__ import annotations

from .base import Frozen
from .version import Version


class Tag(Frozen):
    """A git tag for a package version.

    Tag names follow the convention ``{package_name}/v{version}`` for release tags
    and ``{package_name}/v{version}-base`` for dev-baseline tags. The ``/v`` separator
    lets a single repo host multiple packages without name collisions, and the ``-base``
    suffix distinguishes baseline anchors (used for change detection) from actual releases.
    """

    package_name: str
    raw: str
    version: Version
    is_baseline: bool
    commit: str

    @staticmethod
    def release_tag_name(package_name: str, version: Version) -> str:
        return f"{package_name}/v{version.raw}"

    @staticmethod
    def baseline_tag_name(package_name: str, version: Version) -> str:
        return f"{package_name}/v{version.raw}-base"

    @staticmethod
    def tag_prefix(package_name: str) -> str:
        return f"{package_name}/v"

    @staticmethod
    def is_baseline_tag_name(tag_name: str) -> bool:
        return tag_name.endswith("-base")

    @staticmethod
    def parse_version_from_tag_name(tag_name: str) -> str:
        # Strip package prefix and "-base" suffix to get a bare PEP 440 string.
        ver_str = tag_name.split("/v", 1)[1]
        if ver_str.endswith("-base"):
            ver_str = ver_str[:-5]
        return ver_str
