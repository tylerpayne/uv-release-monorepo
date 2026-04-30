"""SkillUpgradeJob: scaffold or upgrade Claude Code skill files."""

from __future__ import annotations

from pathlib import Path

from diny import singleton, provider

from ...commands import MergeUpgradeCommand, WriteFileCommand
from ...types.job import Job
from ..params.skill_params import SkillParams
from ..shared.git_repo import GitRepo
from ..shared.skill_template import SkillTemplate


@singleton
class SkillUpgradeJob(Job):
    """Upgrade skill template files."""


@provider(SkillUpgradeJob)
def provide_skill_upgrade_job(
    params: SkillParams,
    template: SkillTemplate,
    git_repo: GitRepo,
) -> SkillUpgradeJob:
    if not template.skills:
        raise ValueError("No skill templates found. Is uv-release installed correctly?")

    commands: list[WriteFileCommand | MergeUpgradeCommand] = []

    for skill_name, files in template.skills.items():
        skill_dir = Path(".claude") / "skills" / skill_name
        base_dir = Path(".uvr") / "bases" / ".claude" / "skills" / skill_name

        for skill_file in files:
            target = skill_dir / skill_file.rel_path
            base_path = base_dir / skill_file.rel_path

            if not target.exists():
                commands.append(
                    WriteFileCommand(
                        label=f"Create {target}",
                        path=str(target),
                        content=skill_file.content,
                    )
                )
                commands.append(
                    WriteFileCommand(
                        label=f"Write base for {target}",
                        path=str(base_path),
                        content=skill_file.content,
                    )
                )
                continue

            if params.base_only:
                commands.append(
                    WriteFileCommand(
                        label=f"Update base for {target}",
                        path=str(base_path),
                        content=skill_file.content,
                    )
                )
                continue

            if git_repo.file_is_dirty(str(target)) and not params.force:
                continue

            if params.upgrade:
                base_content = base_path.read_text() if base_path.exists() else ""
                commands.append(
                    MergeUpgradeCommand(
                        label=f"Upgrade {target}",
                        file_path=str(target),
                        base_content=base_content,
                        incoming_content=skill_file.content,
                        base_path=str(base_path),
                        editor=params.editor,
                    )
                )
            elif params.force:
                commands.append(
                    WriteFileCommand(
                        label=f"Overwrite {target}",
                        path=str(target),
                        content=skill_file.content,
                    )
                )
                commands.append(
                    WriteFileCommand(
                        label=f"Update base for {target}",
                        path=str(base_path),
                        content=skill_file.content,
                    )
                )

    return SkillUpgradeJob(name="skill-upgrade", commands=commands)  # type: ignore[arg-type]
