"""Skill management subcommands (init, upgrade)."""

from __future__ import annotations

import argparse

from .init import cmd_skill_init
from .upgrade import cmd_skill_upgrade


def cmd_skill_dispatch(args: argparse.Namespace) -> None:
    """Route to cmd_skill_init or cmd_skill_upgrade based on --upgrade flag."""
    if getattr(args, "upgrade", False):
        cmd_skill_upgrade(args)
    else:
        cmd_skill_init(args)


__all__ = [
    "cmd_skill_dispatch",
    "cmd_skill_init",
    "cmd_skill_upgrade",
]
