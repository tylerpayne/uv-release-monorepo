"""ReuseRun: reuse artifacts from a previous CI run."""

from diny import singleton

from ...types.base import Frozen


@singleton
class ReuseRun(Frozen):
    """If set, download artifacts from this GitHub Actions run ID instead of rebuilding.

    Useful when a previous CI run produced valid build artifacts but a later
    step (e.g. publish) failed — re-running with this ID skips the build job
    and fetches the already-produced artifacts directly from the prior run.
    """

    value: str = ""
