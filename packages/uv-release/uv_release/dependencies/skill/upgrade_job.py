"""SkillUpgradeJob: scaffold or upgrade Claude Code skill files.

Three install modes (mirroring workflow install):
- no flags: scaffold any missing skill files. Files that already exist are
  left untouched (no error, since skills are scaffolded together and an
  individual file may have been added in a later release).
- --upgrade: three-way merge each existing file using the base from the
  previously-recorded skill-version, fetched via uvx.
- --force: overwrite every skill file with the current template.

skill-version in [tool.uvr.config] is updated only after a successful upgrade
or force run. The .uvr/bases/ folder is a transient cache populated by the
fetch command at the start of an --upgrade.
"""

from __future__ import annotations

from pathlib import Path

from diny import singleton, provider

from ... import ui
from ...commands import (
    AnyCommand,
    FetchSkillBasesCommand,
    MergeUpgradeCommand,
    UpdateTomlCommand,
    WriteFileCommand,
)
from ...types.job import Job
from ..config.uvr_config import UvrConfig
from ..params.skill_params import SkillParams
from ..shared.git_repo import GitRepo
from ..shared.skill_template import SkillTemplate


@singleton
class SkillUpgradeJob(Job):
    """Upgrade skill template files."""


_SKILL_BASE_ROOT = Path(".uvr") / "bases" / ".claude" / "skills"

# Backwards-compat fallback for users whose skills predate skill-version
# tracking (added in uv-release 0.32.2). Picked as the first release that
# shipped Claude skills — the oldest plausible baseline. Hand edits stay
# safe because three-way merge surfaces divergent regions as conflicts in
# the editor; only files that are clean upstream get the upgrade applied.
_FALLBACK_SKILL_VERSION = "0.32.0"


@provider(SkillUpgradeJob)
def provide_skill_upgrade_job(
    params: SkillParams,
    template: SkillTemplate,
    git_repo: GitRepo,
    config: UvrConfig,
) -> SkillUpgradeJob:
    if not template.skills:
        msg = "No skill templates found. Is uv-release installed correctly?"
        raise ValueError(msg)

    # --print-template is a pure stdout dump consumed by --upgrade in a newer
    # uvr running us via uvx. Short-circuit here so we never touch the user's
    # cwd state (existence checks, mode requirements, version records). Without
    # this, fetching bases from any older uvr fails whenever the caller's repo
    # already has skill files installed.
    if params.print_template:
        return SkillUpgradeJob(name="skill-upgrade", commands=[])

    commands: list[AnyCommand] = []

    # Scaffold any missing skill files first. Missing files always get written,
    # regardless of mode, so the user picks up newly-added skill files.
    any_existing = False
    for skill_name, files in template.skills.items():
        skill_dir = Path(".claude") / "skills" / skill_name
        for skill_file in files:
            target = skill_dir / skill_file.rel_path
            if not target.exists():
                commands.append(
                    WriteFileCommand(
                        label=f"Create {target}",
                        path=str(target),
                        content=skill_file.content,
                    )
                )
            else:
                any_existing = True

    # If nothing existed before, scaffold-only is enough. Record the version.
    if not any_existing:
        commands.append(
            UpdateTomlCommand(
                label=f"Record skill-version={template.version}",
                key="skill-version",
                value=template.version,
            )
        )
        return SkillUpgradeJob(name="skill-upgrade", commands=commands)

    # Some files exist. Bare `install` is an error: user must pick a mode.
    if not params.upgrade and not params.force:
        msg = (
            "Skill files already exist. "
            "Use --upgrade to three-way-merge with the bundled templates, "
            "or --force to overwrite."
        )
        raise ValueError(msg)

    if params.upgrade:
        # Resolve the merge baseline in priority order:
        #   1. --from-version flag (one-shot override the user just typed)
        #   2. [tool.uvr.config].skill-version (recorded after each --upgrade)
        #   3. _FALLBACK_SKILL_VERSION (oldest known baseline; preserves
        #      hand edits via merge conflicts)
        # Hand edits are always preserved because the three-way merge
        # surfaces divergent regions in the editor rather than overwriting.
        from_version = params.from_version or config.skill_version
        if not from_version:
            from_version = _FALLBACK_SKILL_VERSION
            ui.console.print(
                "  [yellow]No skill-version recorded; falling back to "
                f"uv-release {from_version} as the merge baseline.[/]"
            )
            ui.console.print(
                "  [yellow]Hand edits stay safe — divergent regions land "
                "in your editor as conflicts. Override with [/]"
                "[uvr.cmd]--from-version VERSION[/][yellow].[/]"
            )
        # One fetch populates every base file under .uvr/bases/.claude/skills/.
        commands.append(
            FetchSkillBasesCommand(
                label=f"Fetch skill bases from uv-release {from_version}",
                from_version=from_version,
                output_root=str(_SKILL_BASE_ROOT),
            )
        )
        for skill_name, files in template.skills.items():
            skill_dir = Path(".claude") / "skills" / skill_name
            base_dir = _SKILL_BASE_ROOT / skill_name
            for skill_file in files:
                target = skill_dir / skill_file.rel_path
                if not target.exists():
                    continue
                # Skip dirty files unless --force (which we already excluded).
                if git_repo.file_is_dirty(str(target)):
                    continue
                base_path = base_dir / skill_file.rel_path
                commands.append(
                    MergeUpgradeCommand(
                        label=f"Upgrade {target}",
                        file_path=str(target),
                        base_path=str(base_path),
                        incoming_content=skill_file.content,
                        editor=params.editor,
                    )
                )
    else:
        # --force: overwrite each file with the current template.
        for skill_name, files in template.skills.items():
            skill_dir = Path(".claude") / "skills" / skill_name
            for skill_file in files:
                target = skill_dir / skill_file.rel_path
                if not target.exists():
                    continue
                commands.append(
                    WriteFileCommand(
                        label=f"Overwrite {target}",
                        path=str(target),
                        content=skill_file.content,
                    )
                )

    commands.append(
        UpdateTomlCommand(
            label=f"Record skill-version={template.version}",
            key="skill-version",
            value=template.version,
        )
    )
    return SkillUpgradeJob(name="skill-upgrade", commands=commands)
