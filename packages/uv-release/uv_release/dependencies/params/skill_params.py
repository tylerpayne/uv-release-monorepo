"""SkillParams: parameters for skill subcommand."""

from diny import singleton

from ...types.base import Frozen


@singleton
class SkillParams(Frozen):
    """Seeded by CLI. Controls skill upgrade behavior."""

    force: bool = False
    upgrade: bool = False
    print_template: bool = False
    editor: str = ""
    # One-shot override for the three-way merge baseline. Used when
    # `[tool.uvr.config].skill-version` is missing (skills predate version
    # tracking) or wrong, and the user knows the version they installed with.
    from_version: str = ""
