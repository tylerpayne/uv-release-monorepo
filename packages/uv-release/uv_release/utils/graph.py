"""DAG utilities. Pure functions, no DI."""

from __future__ import annotations

from ..types.package import Package


def topo_sort(nodes: dict[str, list[str]]) -> list[str]:
    """Topological sort of a DAG. nodes maps name -> list of dependencies."""
    # Kahn's algorithm with sorted queues for deterministic output.
    in_degree = {n: 0 for n in nodes}
    reverse: dict[str, list[str]] = {n: [] for n in nodes}
    for name, deps in nodes.items():
        for dep in deps:
            if dep in nodes:
                in_degree[name] += 1
                reverse[dep].append(name)

    queue = sorted(n for n in nodes if in_degree[n] == 0)
    result: list[str] = []
    while queue:
        node = queue.pop(0)
        result.append(node)
        for dependent in sorted(reverse.get(node, [])):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(result) != len(nodes):
        msg = "Dependency cycle detected"
        raise RuntimeError(msg)

    return result


def topo_layers(packages: dict[str, Package]) -> list[list[str]]:
    """Group packages into build layers by dependency depth.

    Layer 0 has no internal deps. Layer N depends on something in layer N-1.
    """
    # Only internal deps constrain build order.
    internal = set(packages.keys())
    deps_map: dict[str, list[str]] = {}
    for name, pkg in packages.items():
        deps_map[name] = [d for d in pkg.dependencies if d in internal]

    order = topo_sort(deps_map)

    # Depth = max(dep depths) + 1. Same-layer packages can build in parallel.
    depth: dict[str, int] = {}
    for name in order:
        pkg_deps = deps_map[name]
        if not pkg_deps:
            depth[name] = 0
        else:
            depth[name] = max(depth[d] for d in pkg_deps if d in depth) + 1

    max_depth = max(depth.values()) if depth else 0
    layers: list[list[str]] = [[] for _ in range(max_depth + 1)]
    for name in order:
        layers[depth[name]].append(name)

    return layers
