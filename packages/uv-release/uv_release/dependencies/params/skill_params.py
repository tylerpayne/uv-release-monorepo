"""SkillParams: parameters for skill subcommand."""

from diny import singleton

from ...types.base import Frozen


@singleton
class SkillParams(Frozen):
    """Seeded by CLI. Controls skill upgrade behavior."""

    force: bool = False
    upgrade: bool = False
    base_only: bool = False
    editor: str = ""
