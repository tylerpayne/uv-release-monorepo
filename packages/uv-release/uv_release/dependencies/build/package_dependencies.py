"""PackageDependencies: classify internal deps as released or needing build."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ...types.package import Package
from ..shared.release_tags import ReleaseTags
from .build_packages import BuildPackages
from ..shared.workspace_packages import WorkspacePackages


class ReleasedDependency(Frozen):
    """An internal dep whose wheel can be downloaded from an existing GitHub release.

    When a dep has already been released, we don't need to build it locally.
    We can fetch the pre-built wheel from the GitHub release identified by
    tag_name and drop it into the deps/ directory.
    """

    package_name: str
    tag_name: str


@singleton
class PackageDependencies(Frozen):
    """Internal deps for build targets, classified by how to resolve them.

    The two lists represent two distinct resolution strategies:
    - released: deps that have a GitHub release tag, so their wheels can be
      downloaded rather than built. Their transitive deps are already bundled
      inside those wheels, so we don't need to recurse into them.
    - needs_build: deps with no release tag that must be built locally first.
      We do recurse into these because their own internal deps also need
      classifying.
    """

    released: list[ReleasedDependency] = []
    """Deps with existing releases. Download their wheels."""

    needs_build: dict[str, Package] = {}
    """Deps with no release. Must be built into deps/."""


@provider(PackageDependencies)
def provide_package_dependencies(
    workspace_packages: WorkspacePackages,
    build_packages: BuildPackages,
    release_tags: ReleaseTags,
) -> PackageDependencies:
    targets = set(build_packages.items.keys())
    released: list[ReleasedDependency] = []
    needs_build: dict[str, Package] = {}
    # seen prevents revisiting and breaks cycles.
    seen: set[str] = set(targets)

    # BFS: released deps stop recursion, unreleased deps enqueue for further walk.
    queue = list(targets)
    while queue:
        name = queue.pop(0)
        pkg = workspace_packages.items.get(name)
        if pkg is None:
            continue
        # Include build-system deps that are workspace packages (#23).
        all_deps = list(pkg.dependencies) + list(pkg.build_dependencies)
        for dep in all_deps:
            if dep in seen or dep not in workspace_packages.items:
                continue
            seen.add(dep)
            tag_name = release_tags.items.get(dep)
            if tag_name:
                released.append(ReleasedDependency(package_name=dep, tag_name=tag_name))
            else:
                needs_build[dep] = workspace_packages.items[dep]
                queue.append(dep)

    return PackageDependencies(released=released, needs_build=needs_build)
