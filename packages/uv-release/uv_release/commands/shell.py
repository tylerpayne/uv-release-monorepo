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
    """Create a git tag. Skips if the tag already exists."""

    type: Literal["create_tag"] = "create_tag"
    tag_name: str

    def execute(self) -> int:
        check = subprocess.run(
            ["git", "tag", "-l", self.tag_name],
            capture_output=True,
            text=True,
        )
        if check.stdout.strip() == self.tag_name:
            if self.label:
                print(f"  {self.label} (already exists, skipping)")
            return 0
        if self.label:
            print(f"  {self.label}")
        result = subprocess.run(["git", "tag", self.tag_name])
        return result.returncode
