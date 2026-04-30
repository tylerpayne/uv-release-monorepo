"""BumpType: which version bump to apply."""

from diny import singleton

from ...types.base import Frozen
from ...types.bump_kind import BumpKind


@singleton
class BumpType(Frozen):
    """Seeded by CLI. Which bump to apply after release."""

    value: BumpKind = BumpKind.DEV
