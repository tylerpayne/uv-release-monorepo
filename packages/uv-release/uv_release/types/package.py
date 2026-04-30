"""A workspace package."""

from __future__ import annotations

from pydantic import Field

from .base import Frozen
from .dependency import Dependency
from .version import Version


class Package(Frozen):
    """A package as discovered from pyproject.toml."""

    name: str
    path: str
    version: Version
    dependencies: list[Dependency] = Field(default_factory=list)
    # Workspace packages in build-system.requires, needed before `uv build` starts.
    build_dependencies: list[Dependency] = Field(default_factory=list)

    def with_version(self, version: Version) -> Package:
        return Package(
            name=self.name,
            path=self.path,
            version=version,
            dependencies=self.dependencies,
            build_dependencies=self.build_dependencies,
        )

    @property
    def dep_names(self) -> list[str]:
        """Normalized names of runtime dependencies."""
        return [d.name for d in self.dependencies]

    @property
    def build_dep_names(self) -> list[str]:
        """Normalized names of build-system dependencies."""
        return [d.name for d in self.build_dependencies]

    @property
    def all_dep_names(self) -> list[str]:
        """All dependency names (runtime + build)."""
        return self.dep_names + self.build_dep_names
