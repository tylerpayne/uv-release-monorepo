"""GitHub release command."""

from __future__ import annotations

import glob
import subprocess
from typing import Literal

from pydantic import Field

from .base import Command


class CreateReleaseCommand(Command):
    """Create a GitHub release with wheel files attached."""

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
        if self.make_latest:
            args.append("--latest")
        else:
            args.append("--latest=false")
        # Expand globs at execution time since wheels don't exist at plan time.
        for pattern in self.files:
            expanded = glob.glob(pattern)
            args.extend(expanded if expanded else [pattern])
        result = subprocess.run(args)
        return result.returncode
