"""Shell and git tag commands."""

from __future__ import annotations

import subprocess
from typing import Literal

from .base import Command


class ShellCommand(Command):
    """Run a subprocess."""

    type: Literal["shell"] = "shell"
    args: list[str]

    def execute(self) -> int:
        if self.label:
            print(f"  {self.label}")
        result = subprocess.run(self.args)
        return result.returncode


class CreateTagCommand(Command):
    """Create a git tag."""

    type: Literal["create_tag"] = "create_tag"
    tag_name: str

    def execute(self) -> int:
        if self.label:
            print(f"  {self.label}")
        result = subprocess.run(["git", "tag", self.tag_name])
        return result.returncode
