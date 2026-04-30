"""NoCommit: skip the commit step."""

from diny import singleton

from ...types.base import Frozen


@singleton
class NoCommit(Frozen):
    """If true, skip git commit after version changes."""

    value: bool = False
