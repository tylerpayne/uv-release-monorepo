"""InstallParams: parameters for the install subcommand."""

from __future__ import annotations

from pydantic import Field

from diny import singleton

from ...types.base import Frozen


@singleton
class InstallParams(Frozen):
    """Seeded by CLI. Packages to install and where to find wheels."""

    packages: list[str] = Field(default_factory=list)
    dist: str = ""
    repo: str = ""
