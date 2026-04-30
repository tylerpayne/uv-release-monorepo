"""Command base class."""

from __future__ import annotations

from ..types.base import Frozen


class Command(Frozen):
    """Base command."""

    type: str
    label: str = ""
    check: bool = True

    def execute(self) -> int:
        raise NotImplementedError
