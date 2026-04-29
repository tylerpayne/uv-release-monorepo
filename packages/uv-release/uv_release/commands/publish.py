"""Package index publishing command."""

from __future__ import annotations

import subprocess
from typing import Literal

from .base import Command


class PublishToIndexCommand(Command):
    """Publish wheels to a package index."""

    type: Literal["publish_to_index"] = "publish_to_index"
    package_name: str
    dist_dir: str = "dist"
    index: str = ""

    def execute(self) -> int:
        if self.label:
            print(f"  {self.label}")
        args = ["uv", "publish", "--dist-dir", self.dist_dir]
        if self.index:
            args.extend(["--index", self.index])
        result = subprocess.run(args)
        return result.returncode
