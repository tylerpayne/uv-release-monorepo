"""Frozen base model for all types."""

from pydantic import BaseModel, ConfigDict


class Frozen(BaseModel):
    """Immutable base. Every type in the system inherits from this."""

    model_config = ConfigDict(frozen=True)
