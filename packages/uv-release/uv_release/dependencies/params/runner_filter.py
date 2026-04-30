"""RunnerFilter: CLI filter for which runners to include in the build matrix."""

from diny import singleton

from ...types.base import Frozen


@singleton
class RunnerFilter(Frozen):
    """Runner labels to include. Empty means all runners."""

    value: frozenset[str] = frozenset()
