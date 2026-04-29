"""DevRelease: whether this is a dev release."""

from diny import singleton

from ...types.base import Frozen


@singleton
class DevRelease(Frozen):
    """Seeded by CLI. If true, release dev versions without stabilizing."""

    value: bool = False
