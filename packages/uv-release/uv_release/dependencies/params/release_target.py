"""ReleaseTarget: CI or local execution."""

from typing import Literal

from diny import singleton

from ...types.base import Frozen


@singleton
class ReleaseTarget(Frozen):
    """Seeded by CLI. Whether to dispatch to CI or run locally."""

    value: Literal["ci", "local"] = "local"
