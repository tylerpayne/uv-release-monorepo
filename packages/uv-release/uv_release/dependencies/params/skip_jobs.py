"""SkipJobs: jobs to skip in the release pipeline."""

from diny import singleton

from ...types.base import Frozen


@singleton
class SkipJobs(Frozen):
    """Set of job names to skip."""

    value: frozenset[str] = frozenset()
