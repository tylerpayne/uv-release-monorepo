"""Package index publishing command."""

from __future__ import annotations

import subprocess
from pathlib import Path
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
        # Glob for wheels matching this package in the dist directory.
        dist_name = self.package_name.replace("-", "_")
        wheels = list(Path(self.dist_dir).glob(f"{dist_name}-*.whl"))
        if not wheels:
            print(f"    No wheels found for {self.package_name} in {self.dist_dir}")
            return 1
        args = ["uv", "publish"]
        if self.index:
            args.extend(["--index", self.index])
        args.extend(str(w) for w in wheels)
        result = subprocess.run(args)
        return result.returncode
