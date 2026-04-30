"""UserReleaseNotes: user-provided release notes from CLI."""

from diny import singleton

from ...types.base import Frozen


@singleton
class UserReleaseNotes(Frozen):
    """Package name -> user-provided notes. Overrides auto-generated notes."""

    items: dict[str, str] = {}
