"""Build command."""

from __future__ import annotations

import subprocess
from typing import Literal

from .base import Command


class BuildCommand(Command):
    """Build a package with uv build."""

    type: Literal["build"] = "build"
    package_path: str
    out_dir: str = "dist"

    def execute(self) -> int:
        if self.label:
            print(f"  {self.label}")
        result = subprocess.run(
            [
                "uv",
                "build",
                self.package_path,
                "--out-dir",
                self.out_dir,
                # --find-links tells uv where to find pre-built workspace deps.
                # dist/ has release targets, deps/ has unreleased internal deps.
                "--find-links",
                "dist",
                "--find-links",
                "deps",
                # --no-sources prevents uv from resolving workspace deps from
                # source, forcing it to use only the pre-built wheels.
                "--no-sources",
            ]
        )
        return result.returncode
