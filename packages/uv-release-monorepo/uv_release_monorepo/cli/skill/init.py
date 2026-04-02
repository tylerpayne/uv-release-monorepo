"""The ``uvr skill init`` command."""

from __future__ import annotations

import argparse
from importlib.resources import files
from pathlib import Path

from ...shared.utils.cli import fatal
from ...shared.utils.toml import read_pyproject, write_pyproject
from .._args import CommandArgs
from .._upgrade import write_base


_SKILL_FILES: dict[str, list[str]] = {
    "release": [
        "SKILL.md",
        "references/cmd-init.md",
        "references/cmd-install.md",
        "references/cmd-release.md",
        "references/cmd-runners.md",
        "references/cmd-skill-init.md",
        "references/cmd-status.md",
        "references/cmd-validate.md",
        "references/custom-jobs.md",
        "references/dev-releases.md",
        "references/pipeline.md",
        "references/post-releases.md",
        "references/pre-releases.md",
        "references/release-plan.md",
        "references/troubleshooting.md",
    ],
}

_SKILLS_TEMPLATE_DIR = files("uv_release_monorepo").joinpath("templates/skills")


class SkillInitArgs(CommandArgs):
    """Typed arguments for ``uvr skill init``."""

    force: bool = False
    upgrade: bool = False
    base_only: bool = False
    editor: str | None = None


def _load_skill_file(skill_name: str, rel_path: str) -> str:
    """Load a skill file from the bundled template directory."""
    base = Path(str(_SKILLS_TEMPLATE_DIR))
    path = base / skill_name / rel_path
    return path.read_text(encoding="utf-8")


def _store_skill_version(root: Path) -> None:
    """Store the current uvr package version as skill_version in [tool.uvr.config]."""
    from ...shared.utils.cli import __version__

    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return
    doc = read_pyproject(pyproject)
    tool = doc.setdefault("tool", {})
    uvr = tool.setdefault("uvr", {})
    config = uvr.setdefault("config", {})
    config["skill_version"] = __version__
    # Remove legacy key if present
    config.pop("skill_init_commit", None)
    write_pyproject(pyproject, doc)


def cmd_skill_init(args: argparse.Namespace) -> None:
    """Copy bundled Claude Code skills into the current project."""
    from ...shared.utils.cli import __version__

    parsed = SkillInitArgs.from_namespace(args)
    root = Path.cwd()

    if parsed.base_only:
        # --base-only: write merge bases without touching actual files
        count = 0
        for skill_name in _SKILL_FILES:
            for rel_path in _SKILL_FILES[skill_name]:
                rel_dest = f".claude/skills/{skill_name}/{rel_path}"
                write_base(root, rel_dest, _load_skill_file(skill_name, rel_path))
                count += 1
        print(f"OK: Wrote {count} merge bases for skills (uvr v{__version__})")
        return

    if not (root / ".git").exists():
        fatal("Not a git repository. Run from the repo root.")

    dest_base = root / ".claude" / "skills"

    written = 0
    skipped = 0
    for skill_name in _SKILL_FILES:
        for rel_path in _SKILL_FILES[skill_name]:
            dest = dest_base / skill_name / rel_path
            if dest.exists() and not parsed.force:
                print(f"  skip  {skill_name}/{rel_path} (exists)")
                skipped += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = _load_skill_file(skill_name, rel_path)
            dest.write_text(content, encoding="utf-8")
            # Save merge base
            rel_dest = f".claude/skills/{skill_name}/{rel_path}"
            write_base(root, rel_dest, content)
            print(f"  write {skill_name}/{rel_path}")
            written += 1

    print()
    if written:
        _store_skill_version(root)
        from ...shared.utils.cli import __version__

        print(f"OK: Wrote {written} file(s) to .claude/skills/ (uvr v{__version__})")
    if skipped:
        print(f"  Skipped {skipped} existing file(s). Use --force to overwrite.")
    if not written and not skipped:
        print("Nothing to do.")
        return

    print()
    print("Next steps:")
    print("  1. Review .claude/skills/release/SKILL.md and tailor to your project")
    print("  2. Commit the skill files")
    print("  3. Use /release in Claude Code to start a release")
