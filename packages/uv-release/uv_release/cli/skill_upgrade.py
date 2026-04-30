"""uvr skill upgrade: scaffold or upgrade Claude Code skill files."""

from __future__ import annotations

from diny import inject

from ..dependencies.skill.upgrade_job import SkillUpgradeJob
from ..execute import execute_job


@inject
def cmd_skill_upgrade(upgrade_job: SkillUpgradeJob) -> None:
    if not upgrade_job.commands:
        print("Skills are already up to date.")
        return

    execute_job(upgrade_job)
