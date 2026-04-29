"""ConfigureParams: parameters for configure subcommands."""

from __future__ import annotations

from pydantic import Field

from diny import singleton

from ...types.base import Frozen


@singleton
class ConfigureParams(Frozen):
    """Seeded by CLI. Configuration values to set."""

    latest: str | None = None
    include_packages: list[str] = Field(default_factory=list)
    exclude_packages: list[str] = Field(default_factory=list)
    remove_packages: list[str] = Field(default_factory=list)
    clear: bool = False


@singleton
class ConfigurePublishParams(Frozen):
    """Seeded by CLI. Publishing configuration values to set."""

    index: str | None = None
    environment: str | None = None
    trusted_publishing: str | None = None
    include_packages: list[str] = Field(default_factory=list)
    exclude_packages: list[str] = Field(default_factory=list)
    remove_packages: list[str] = Field(default_factory=list)
    clear: bool = False


@singleton
class ConfigureRunnersParams(Frozen):
    """Seeded by CLI. Runner configuration values to set."""

    package: str = ""
    add: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)
    clear: bool = False
