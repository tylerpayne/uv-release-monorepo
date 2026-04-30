"""DryRun: preview mode with no side effects."""

from __future__ import annotations

from diny import singleton

from ...types.base import Frozen


@singleton
class DryRun(Frozen):
    """If true, show what would happen without executing."""

    value: bool = False
