"""GitHub release command."""

from __future__ import annotations

import subprocess
from typing import Literal

from pydantic import Field

from .base import Command


class CreateReleaseCommand(Command):
    """Create a GitHub release."""

    type: Literal["create_release"] = "create_release"
    tag_name: str
    title: str
    notes: str
    files: list[str] = Field(default_factory=list)
    make_latest: bool = False

    def execute(self) -> int:
        if self.label:
            print(f"  {self.label}")
        args = [
            "gh",
            "release",
            "create",
            self.tag_name,
            "--title",
            self.title,
            "--notes",
            self.notes,
        ]
        # Explicit --latest=false prevents GitHub from auto-promoting pre-releases.
        if self.make_latest:
            args.append("--latest")
        else:
            args.append("--latest=false")
        args.extend(self.files)
        result = subprocess.run(args)
        return result.returncode
