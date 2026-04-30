"""Dependency name parsing. Pure function, no DI."""

from __future__ import annotations

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def parse_dep_name(dep_str: str) -> str:
    """Extract the PEP 503 normalized package name from a dependency specifier."""
    return canonicalize_name(Requirement(dep_str).name)
