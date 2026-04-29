"""UvrConfig: workspace-level release configuration."""

from __future__ import annotations

from pathlib import Path

import tomlkit
from diny import singleton, provider

from ...types.base import Frozen
from ...types.pyproject import RootPyProject


@singleton
class UvrConfig(Frozen):
    """From [tool.uvr.config]."""

    latest_package: str = ""
    python_version: str = "3.12"
    include: frozenset[str] = frozenset()
    exclude: frozenset[str] = frozenset()


@provider(UvrConfig)
def provide_uvr_config() -> UvrConfig:
    doc = RootPyProject.model_validate(
        tomlkit.loads(Path("pyproject.toml").read_text())
    )
    config = doc.tool.uvr.config
    return UvrConfig(
        latest_package=config.latest,
        python_version=config.python_version,
        include=frozenset(config.include),
        exclude=frozenset(config.exclude),
    )
