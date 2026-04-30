"""WorkflowTemplate: the bundled release workflow template."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen


@singleton
class WorkflowTemplate(Frozen):
    """The bundled workflow template content, loaded from package resources."""

    content: str = ""
    version: str = ""


@provider(WorkflowTemplate)
def provide_workflow_template() -> WorkflowTemplate:
    try:
        import importlib.resources as resources

        ref = resources.files("uv_release") / "templates" / "release" / "release.yml"
        content = ref.read_text(encoding="utf-8")
    except (FileNotFoundError, TypeError, ModuleNotFoundError):
        content = ""

    try:
        from importlib.metadata import version as pkg_version

        ver = pkg_version("uv-release")
    except Exception:
        ver = "0.0.0"

    return WorkflowTemplate(content=content, version=ver)
