"""Job base class and subclasses for DI identity."""

from __future__ import annotations

from pydantic import Field, SerializeAsAny

from .base import Frozen
from ..commands import AnyCommand


class Job(Frozen):
    """A named sequence of commands.

    Subclasses of Job exist purely for dependency-injection identity: the planner
    distinguishes job types by their Python type, not by a string discriminator. Using
    distinct subclasses means each job kind can be declared as a typed parameter on
    intent methods and resolved unambiguously by the DI system.
    """

    name: str
    # SerializeAsAny prevents Pydantic from dropping subclass-specific fields.
    commands: list[SerializeAsAny[AnyCommand]] = Field(default_factory=list)
