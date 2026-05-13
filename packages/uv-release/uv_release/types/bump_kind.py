"""Version bump strategies."""

from enum import Enum


class BumpKind(Enum):
    """Version bump strategies."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    POST = "post"
    DEV = "dev"
    # Pre-release kinds. Same-kind input increments pre_number; higher kind
    # resets to 0; lower kind (e.g. rc -> alpha) is a regression and is rejected.
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"
    # Strips only the .devN suffix, preserving any pre-release or post
    # suffix. This is the operation the release pipeline uses to turn a
    # working-tree dev version into the version it actually publishes.
    RELEASE = "release"
    # Strips pre/dev suffix to produce a clean release.
    STABLE = "stable"
    # Auto-detect the last version section and increment its number.
    AUTO = "auto"
