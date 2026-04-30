"""A parsed dependency specifier."""

from __future__ import annotations

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version as PkgVersion

from .base import Frozen


class Dependency(Frozen):
    """A parsed PEP 508 dependency specifier."""

    name: str
    specifier: str
    raw: str

    @staticmethod
    def parse(dep_str: str) -> Dependency:
        req = Requirement(dep_str)
        return Dependency(
            name=canonicalize_name(req.name),
            specifier=str(req.specifier),
            raw=dep_str,
        )

    def satisfied_by(self, version: str) -> bool:
        """Check if a version string satisfies this dependency's specifier."""
        if not self.specifier:
            return True
        req = Requirement(self.raw)
        return req.specifier.contains(PkgVersion(version))
