"""A package planned for release."""

from __future__ import annotations

from .base import Frozen
from .version import Version


class Release(Frozen):
    """A package being released, with its current, release, and next versions."""

    name: str
    current_version: Version
    release_version: Version
    next_version: Version
    baseline_tag: str = ""
