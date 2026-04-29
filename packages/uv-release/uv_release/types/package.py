"""A workspace package."""

from __future__ import annotations

from pydantic import Field

from .base import Frozen
from .version import Version


class Package(Frozen):
    """A package as discovered from pyproject.toml."""

    name: str
    path: str
    version: Version
    dependencies: list[str] = Field(default_factory=list)
    # Workspace packages in build-system.requires, needed before `uv build` starts.
    build_dependencies: list[str] = Field(default_factory=list)

    def with_version(self, version: Version) -> Package:
        return Package(
            name=self.name,
            path=self.path,
            version=version,
            dependencies=self.dependencies,
            build_dependencies=self.build_dependencies,
        )
