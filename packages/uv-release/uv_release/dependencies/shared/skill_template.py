"""SkillTemplate: bundled skill templates."""

from __future__ import annotations

from pydantic import Field

from diny import singleton, provider

from ...types.base import Frozen


class SkillFile(Frozen):
    """A single skill template file."""

    rel_path: str
    content: str


@singleton
class SkillTemplate(Frozen):
    """All bundled skill templates, organized by skill name."""

    skills: dict[str, list[SkillFile]] = Field(default_factory=dict)
    version: str = ""


@provider(SkillTemplate)
def provide_skill_template() -> SkillTemplate:
    try:
        import importlib.resources as resources

        skills_dir = resources.files("uv_release") / "templates" / "skills"
        skills: dict[str, list[SkillFile]] = {}
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_name = skill_dir.name
            files: list[SkillFile] = []
            for f in skill_dir.iterdir():
                if f.is_file():
                    files.append(
                        SkillFile(
                            rel_path=f.name,
                            content=f.read_text(encoding="utf-8"),
                        )
                    )
            if files:
                skills[skill_name] = files
    except (FileNotFoundError, TypeError, ModuleNotFoundError):
        skills = {}

    try:
        from importlib.metadata import version as pkg_version

        ver = pkg_version("uv-release")
    except Exception:
        ver = "0.0.0"

    return SkillTemplate(skills=skills, version=ver)
