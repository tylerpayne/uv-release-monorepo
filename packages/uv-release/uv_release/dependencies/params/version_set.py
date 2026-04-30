"""VersionSet: explicit version string from --set flag."""

from diny import singleton

from ...types.base import Frozen


@singleton
class VersionSet(Frozen):
    """If non-empty, set all targeted packages to this exact version."""

    value: str = ""
