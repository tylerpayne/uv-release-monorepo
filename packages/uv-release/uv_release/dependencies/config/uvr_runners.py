"""UvrRunners: per-package CI runner configuration."""

from __future__ import annotations

from pathlib import Path

import tomlkit
from diny import singleton, provider

from ...types.base import Frozen
from ...types.pyproject import RootPyProject


@singleton
class UvrRunners(Frozen):
    """From [tool.uvr.runners]. Maps package name to runner label lists."""

    # { pkg: [[label, ...], ...] } -- each inner list is one CI matrix row.
    items: dict[str, list[list[str]]] = {}


@provider(UvrRunners)
def provide_uvr_runners() -> UvrRunners:
    doc = RootPyProject.model_validate(
        tomlkit.loads(Path("pyproject.toml").read_text())
    )
    return UvrRunners(items=doc.tool.uvr.runners)
