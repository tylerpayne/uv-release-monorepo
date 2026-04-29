"""UvrPublishing: index publishing configuration."""

from __future__ import annotations

from pathlib import Path

import tomlkit
from diny import singleton, provider

from ...types.base import Frozen
from ...types.pyproject import RootPyProject


@singleton
class UvrPublishing(Frozen):
    """From [tool.uvr.publish]."""

    index: str = ""
    environment: str = ""
    # PyPI trusted publishing default: OIDC inferred from GHA environment.
    trusted_publishing: str = "automatic"
    include: frozenset[str] = frozenset()
    exclude: frozenset[str] = frozenset()


@provider(UvrPublishing)
def provide_uvr_publishing() -> UvrPublishing:
    doc = RootPyProject.model_validate(
        tomlkit.loads(Path("pyproject.toml").read_text())
    )
    publish = doc.tool.uvr.publish
    return UvrPublishing(
        index=publish.index,
        environment=publish.environment,
        trusted_publishing=publish.trusted_publishing,
        include=frozenset(publish.include),
        exclude=frozenset(publish.exclude),
    )
