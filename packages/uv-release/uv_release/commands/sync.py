"""Lockfile sync command."""

from __future__ import annotations

import subprocess
from typing import Literal

from .base import Command


class SyncLockfileCommand(Command):
    """uv sync after version changes. Non-zero exit is sometimes expected."""

    type: Literal["sync_lockfile"] = "sync_lockfile"
    check: bool = False

    def execute(self) -> int:
        if self.label:
            print(f"  {self.label}")
        result = subprocess.run(
            ["uv", "sync", "--all-groups", "--all-extras", "--all-packages"]
        )
        return result.returncode
