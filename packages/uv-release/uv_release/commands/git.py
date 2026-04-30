"""Git workflow commands: identity, commit, push."""

from __future__ import annotations

import subprocess
from typing import Literal

from .base import Command


class ConfigureGitIdentityCommand(Command):
    """Set git user.name and user.email for CI runners."""

    type: Literal["configure_git_identity"] = "configure_git_identity"

    def execute(self) -> int:
        if self.label:
            print(f"  {self.label}")
        result = subprocess.run(["git", "config", "user.name", "github-actions[bot]"])
        if result.returncode != 0:
            return result.returncode
        result = subprocess.run(
            [
                "git",
                "config",
                "user.email",
                "github-actions[bot]@users.noreply.github.com",
            ]
        )
        return result.returncode


class CommitCommand(Command):
    """git commit -am with a message and optional body. Skips if nothing to commit."""

    type: Literal["commit"] = "commit"
    message: str
    body: str = ""

    def execute(self) -> int:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
        if not status.stdout.strip():
            if self.label:
                print(f"  {self.label} (nothing to commit, skipping)")
            return 0
        if self.label:
            print(f"  {self.label}")
        args = ["git", "commit", "-am", self.message]
        if self.body:
            args.extend(["-m", self.body])
        result = subprocess.run(args)
        return result.returncode


class PushCommand(Command):
    """git push, optionally preceded by pull --rebase."""

    type: Literal["push"] = "push"
    follow_tags: bool = True
    pull_rebase: bool = False

    def execute(self) -> int:
        if self.label:
            print(f"  {self.label}")
        if self.pull_rebase:
            result = subprocess.run(["git", "pull", "--rebase"])
            if result.returncode != 0:
                return result.returncode
        args = ["git", "push"]
        if self.follow_tags:
            args.append("--follow-tags")
        result = subprocess.run(args)
        return result.returncode
