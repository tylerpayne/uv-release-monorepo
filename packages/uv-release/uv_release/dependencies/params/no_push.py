"""NoPush: skip the push step."""

from diny import singleton

from ...types.base import Frozen


@singleton
class NoPush(Frozen):
    """If true, skip git push after committing."""

    value: bool = False
