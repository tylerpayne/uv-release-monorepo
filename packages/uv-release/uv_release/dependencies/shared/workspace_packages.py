"""WorkspacePackages: all packages in the workspace."""

from __future__ import annotations

from pathlib import Path


import tomlkit
from diny import singleton, provider
from packaging.utils import canonicalize_name

from ...types.base import Frozen
from ...types.package import Package
from ...types.pyproject import PackagePyProject, RootPyProject
from ...types.version import Version
from ...utils.deps import parse_dep_name


@singleton
class WorkspacePackages(Frozen):
    """All packages discovered from the workspace."""

    items: dict[str, Package]
    root: Path


@provider(WorkspacePackages)
def provide_workspace_packages() -> WorkspacePackages:
    root = Path(".")
    root_doc = RootPyProject.model_validate(
        tomlkit.loads((root / "pyproject.toml").read_text())
    )

    packages: dict[str, Package] = {}
    for pattern in root_doc.tool.uv.workspace.members:
        for pkg_dir in sorted(root.glob(pattern)):
            pyproject_path = pkg_dir / "pyproject.toml"
            if not pyproject_path.exists():
                continue

            pkg_doc = PackagePyProject.model_validate(
                tomlkit.loads(pyproject_path.read_text())
            )
            name = canonicalize_name(pkg_doc.project.name or pkg_dir.name)
            version = Version.parse(pkg_doc.project.version or "0.0.0")

            dep_names = [parse_dep_name(d) for d in pkg_doc.project.dependencies]

            # Include build-system.requires workspace deps in build plan (#23).
            build_dep_names = [parse_dep_name(d) for d in pkg_doc.build_system.requires]

            packages[name] = Package(
                name=name,
                path=str(pkg_dir),
                version=version,
                dependencies=dep_names,
                build_dependencies=build_dep_names,
            )

    return WorkspacePackages(items=packages, root=root)
