"""Build command."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Literal

from pydantic import Field

from .base import Command


class BuildCommand(Command):
    """Build a package with uv build."""

    type: Literal["build"] = "build"
    package_path: str
    out_dir: str = "dist"
    # All runners this package needs to build on (own + inherited from dependents).
    runners: list[list[str]] = Field(default_factory=list)
    # Runners where this package is an actual release target (wheel goes to dist/).
    # On other runners the wheel goes to deps/ so dependents can find it.
    target_runners: list[list[str]] = Field(default_factory=list)

    def execute(self) -> int:
        # In CI, UVR_RUNNER is set to the current runner's labels as JSON.
        # Skip this build if the current runner is not in the package's runner list.
        if self.runners and not self._runner_matches():
            if self.label:
                print(f"  {self.label} (skipped, wrong runner)")
            return 0
        # On a runner where this package is only a dependency (not a target),
        # output to deps/ instead of dist/.
        out_dir = self._effective_out_dir()
        if self.label:
            print(f"  {self.label}")
        result = subprocess.run(
            [
                "uv",
                "build",
                self.package_path,
                "--out-dir",
                out_dir,
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

    def _runner_matches(self) -> bool:
        """Check if the current CI runner matches any of this package's runners."""
        raw = os.environ.get("UVR_RUNNER", "")
        if not raw:
            return True
        try:
            current = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return True
        if not isinstance(current, list):
            return True
        return current in self.runners

    def _effective_out_dir(self) -> str:
        """Determine output dir based on current runner.

        If this is a target on the current runner, output to dist/.
        If this is only building as a dependency, output to deps/.
        Without UVR_RUNNER (local builds), use the configured out_dir.
        """
        if not self.target_runners:
            return self.out_dir
        raw = os.environ.get("UVR_RUNNER", "")
        if not raw:
            return self.out_dir
        try:
            current = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return self.out_dir
        if not isinstance(current, list):
            return self.out_dir
        if current in self.target_runners:
            return "dist"
        return "deps"
