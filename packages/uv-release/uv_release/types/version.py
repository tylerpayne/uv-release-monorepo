"""PEP 440 version, parsed once into structured fields."""

from __future__ import annotations

from enum import Enum

from packaging.version import Version as PkgVersion

from .base import Frozen

# Normalize pre-release label aliases to canonical short forms.
_PRE_KIND_MAP: dict[str, str] = {
    "a": "a",
    "alpha": "a",
    "b": "b",
    "beta": "b",
    "rc": "rc",
    "c": "rc",
}


class VersionState(Enum):
    """The 11 distinct forms a version can take."""

    CLEAN_STABLE = "X.Y.Z"
    DEV0_STABLE = "X.Y.Z.dev0"
    DEVK_STABLE = "X.Y.Z.devK"
    CLEAN_PRE0 = "X.Y.Za0"
    CLEAN_PREN = "X.Y.ZaN"
    DEV0_PRE = "X.Y.ZaN.dev0"
    DEVK_PRE = "X.Y.ZaN.devK"
    CLEAN_POST0 = "X.Y.Z.post0"
    CLEAN_POSTM = "X.Y.Z.postM"
    DEV0_POST = "X.Y.Z.postM.dev0"
    DEVK_POST = "X.Y.Z.postM.devK"


class Version(Frozen):
    """A PEP 440 version, parsed once into structured fields."""

    raw: str
    state: VersionState
    major: int
    minor: int
    patch: int
    is_dev: bool
    dev_number: int | None = None
    pre_kind: str | None = None
    pre_number: int | None = None
    post_number: int | None = None

    @property
    def base(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @staticmethod
    def parse(raw: str) -> Version:
        """Parse a PEP 440 version string into a frozen Version."""
        pv = PkgVersion(raw)
        pre_kind: str | None = None
        pre_number: int | None = None
        if pv.pre is not None:
            pre_kind = _PRE_KIND_MAP.get(pv.pre[0], pv.pre[0])
            pre_number = pv.pre[1]
        post_number = pv.post if pv.post is not None else None
        dev_number = pv.dev if pv.dev is not None else None
        is_dev = dev_number is not None
        state = _classify(pre_kind, pre_number, post_number, dev_number)
        return Version(
            # Use canonical form from packaging for round-trip safety.
            raw=str(pv),
            state=state,
            major=pv.major,
            minor=pv.minor,
            patch=pv.micro,
            is_dev=is_dev,
            dev_number=dev_number,
            pre_kind=pre_kind,
            pre_number=pre_number,
            post_number=post_number,
        )

    @staticmethod
    def build(
        base: str,
        *,
        pre_kind: str | None = None,
        pre_number: int | None = None,
        post_number: int | None = None,
        dev_number: int | None = None,
    ) -> Version:
        """Construct a Version from components."""
        # Assemble then re-parse to guarantee consistent canonicalization.
        raw = base
        if pre_kind is not None:
            raw += f"{pre_kind}{pre_number if pre_number is not None else 0}"
        if post_number is not None:
            raw += f".post{post_number}"
        if dev_number is not None:
            raw += f".dev{dev_number}"
        return Version.parse(raw)

    def with_dev(self, dev_number: int) -> Version:
        return Version.build(
            self.base,
            pre_kind=self.pre_kind,
            pre_number=self.pre_number,
            post_number=self.post_number,
            dev_number=dev_number,
        )

    def without_dev(self) -> Version:
        return Version.build(
            self.base,
            pre_kind=self.pre_kind,
            pre_number=self.pre_number,
            post_number=self.post_number,
        )

    def bump_major(self) -> Version:
        return Version.build(f"{self.major + 1}.0.0")

    def bump_minor(self) -> Version:
        return Version.build(f"{self.major}.{self.minor + 1}.0")

    def bump_patch(self) -> Version:
        return Version.build(f"{self.major}.{self.minor}.{self.patch + 1}")


def _classify(
    pre_kind: str | None,
    pre_number: int | None,
    post_number: int | None,
    dev_number: int | None,
) -> VersionState:
    has_pre = pre_kind is not None
    has_post = post_number is not None
    has_dev = dev_number is not None

    # Priority: post > pre > dev > clean stable.
    if has_post:
        if has_dev:
            return (
                VersionState.DEVK_POST
                if dev_number and dev_number > 0
                else VersionState.DEV0_POST
            )
        return (
            VersionState.CLEAN_POSTM
            if post_number and post_number > 0
            else VersionState.CLEAN_POST0
        )

    if has_pre:
        if has_dev:
            return (
                VersionState.DEVK_PRE
                if dev_number and dev_number > 0
                else VersionState.DEV0_PRE
            )
        return (
            VersionState.CLEAN_PREN
            if pre_number and pre_number > 0
            else VersionState.CLEAN_PRE0
        )

    if has_dev:
        return (
            VersionState.DEVK_STABLE
            if dev_number and dev_number > 0
            else VersionState.DEV0_STABLE
        )

    return VersionState.CLEAN_STABLE
