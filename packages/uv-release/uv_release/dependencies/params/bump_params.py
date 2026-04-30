"""BumpParams: extra flags for standalone bump command."""

from diny import singleton

from ...types.base import Frozen


@singleton
class NoPinDeps(Frozen):
    """If true, skip dependency pinning after version bump."""

    value: bool = False
