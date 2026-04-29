"""ReuseReleases: skip creating GitHub releases."""

from diny import singleton

from ...types.base import Frozen


@singleton
class ReuseReleases(Frozen):
    """If true, skip creating git tags and GitHub releases.

    Useful when re-running a release pipeline that already created the tags
    and GitHub releases in a previous attempt — trying to create them again
    would fail, so this flag lets the rest of the pipeline (e.g. publish)
    proceed without the tag/release steps.
    """

    value: bool = False
