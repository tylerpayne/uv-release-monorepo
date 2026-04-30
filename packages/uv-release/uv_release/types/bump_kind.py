"""The 9 version bump strategies."""

from enum import Enum


class BumpKind(Enum):
    """The 9 version bump strategies."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"
    POST = "post"
    DEV = "dev"
    # Strips pre/dev suffix to produce a clean release.
    STABLE = "stable"
