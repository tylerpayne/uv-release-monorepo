"""Hooks: lifecycle callbacks for the release pipeline."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from diny import singleton, provider


_DEFAULT_FILE = "uvr_hooks.py"
_DEFAULT_CLASS = "Hooks"


@singleton
class Hooks:
    """Lifecycle hooks. Subclass in a uvr_hooks.py file to customize.

    Configure via [tool.uvr.hooks].file = "path/to/hooks.py:MyHooks"
    in pyproject.toml. Falls back to uvr_hooks.py:Hooks in the workspace
    root if that file exists.

    Per-job hooks (pre_build, post_build, etc.) are called by the executor
    via getattr, so any method named pre_{job_name} or post_{job_name} will
    be invoked at the right time.
    """

    def pre_plan(self, root: Path, command: str) -> None:
        pass

    def post_plan(self, root: Path, command: str, plan: Any) -> Any:
        return plan

    def pre_command(self, job_name: str, command: Any) -> None:
        pass

    def post_command(self, job_name: str, command: Any, returncode: int) -> None:
        pass

    def pre_build(self) -> None:
        pass

    def post_build(self) -> None:
        pass

    def pre_release(self) -> None:
        pass

    def post_release(self) -> None:
        pass

    def pre_publish(self) -> None:
        pass

    def post_publish(self) -> None:
        pass

    def pre_bump(self) -> None:
        pass

    def post_bump(self) -> None:
        pass


@provider(Hooks)
def provide_hooks() -> Hooks:
    """Load user hooks from pyproject.toml config or fallback file.

    Checks [tool.uvr.hooks].file for a "path:ClassName" spec. If not
    configured, looks for uvr_hooks.py in the workspace root. Returns
    a default no-op Hooks instance if neither exists.
    """
    import tomlkit

    from ...types.pyproject import RootPyProject

    root = Path(".")
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return Hooks()

    doc = RootPyProject.model_validate(tomlkit.loads(pyproject_path.read_text()))

    if doc.tool.uvr.hooks.file:
        return _load_from_spec(root, doc.tool.uvr.hooks.file)

    fallback = root / _DEFAULT_FILE
    if fallback.exists():
        return _load_from_spec(root, f"{_DEFAULT_FILE}:{_DEFAULT_CLASS}")

    return Hooks()


def _load_from_spec(root: Path, spec: str) -> Hooks:
    """Load a Hooks subclass from a 'path:ClassName' spec."""
    if ":" in spec:
        file_path, class_name = spec.rsplit(":", 1)
    else:
        file_path = spec
        class_name = _DEFAULT_CLASS

    full_path = root / file_path
    if not full_path.exists():
        msg = f"Hook file not found: {full_path}"
        raise FileNotFoundError(msg)

    module_spec = importlib.util.spec_from_file_location("_uvr_hooks", full_path)
    if module_spec is None or module_spec.loader is None:
        msg = f"Cannot load hook module: {full_path}"
        raise ImportError(msg)

    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    hook_class = getattr(module, class_name, None)
    if hook_class is None:
        msg = f"Hook class {class_name!r} not found in {full_path}"
        raise AttributeError(msg)

    return hook_class()
