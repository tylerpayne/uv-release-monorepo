"""Base class for injectable state types."""

from __future__ import annotations

from diny import singleton
from pydantic import BaseModel, ConfigDict


@singleton
class State(BaseModel):
    """Base for all injectable state types.

    Subclasses define a module-level @provider function that declares
    dependencies via type hints. diny inspects the provider and
    recursively resolves each dependency before calling it.
    """

    model_config = ConfigDict(frozen=True)
