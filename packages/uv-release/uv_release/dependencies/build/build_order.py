"""BuildOrder: build targets + deps grouped into layers by dependency depth."""

from __future__ import annotations

from diny import singleton, provider

from ...types.base import Frozen
from ...types.package import Package
from ...utils.graph import topo_layers
from .build_packages import BuildPackages
from .package_dependencies import PackageDependencies


class BuildItem(Frozen):
    """A single package to build, with its output directory.

    out_dir determines where the produced wheel lands after the build:
    - "dist": release targets whose wheels will be uploaded to a GitHub release.
    - "deps": unreleased internal deps whose wheels are only consumed locally
      during the build of packages that depend on them.
    """

    name: str
    package: Package
    out_dir: str  # "dist" for targets, "deps" for unreleased deps


@singleton
class BuildOrder(Frozen):
    """Packages to build, grouped into layers. Layer 0 has no internal deps."""

    layers: list[list[BuildItem]]


@provider(BuildOrder)
def provide_build_order(
    build_packages: BuildPackages,
    package_dependencies: PackageDependencies,
) -> BuildOrder:
    # Merge targets and unreleased deps for correct layer assignment.
    all_to_build = {**package_dependencies.needs_build, **build_packages.items}
    targets = set(build_packages.items.keys())
    raw_layers = topo_layers(all_to_build)

    layers: list[list[BuildItem]] = []
    for raw_layer in raw_layers:
        layer: list[BuildItem] = []
        for name in raw_layer:
            is_target = name in targets
            layer.append(
                BuildItem(
                    name=name,
                    package=all_to_build[name],
                    out_dir="dist" if is_target else "deps",
                )
            )
        layers.append(layer)

    return BuildOrder(layers=layers)
