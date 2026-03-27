"""Change detection: determine which packages need rebuilding."""

from __future__ import annotations

from collections.abc import Mapping


from .models import PackageInfo
from .shell import git, step


def detect_changes(
    packages: dict[str, PackageInfo],
    baselines: Mapping[str, str | None],
    rebuild_all: bool,
) -> list[str]:
    """Determine which packages need to be rebuilt.

    A package is "dirty" and needs rebuilding if:
    1. rebuild_all is True (rebuild everything)
    2. No previous baseline tag exists for the package (first release)
    3. Any file in the package directory changed since its baseline
    4. Root pyproject.toml changed since its baseline (workspace-level config
       such as dependency overrides or build settings can affect any package,
       so root changes conservatively trigger a rebuild for all packages)
    5. Any of its dependencies are dirty (transitive dirtiness)

    The baseline tag ({pkg}/v{version}-base) is placed on the version
    bump commit after each release, so only real work after the bump
    shows up in the diff.

    Args:
        packages: Map of package name -> PackageInfo.
        baselines: Map of package name -> baseline tag (or None).
        rebuild_all: If True, mark all packages as dirty.

    Returns:
        List of changed package names.
    """
    step("Detecting changes")

    if rebuild_all:
        dirty = set(packages.keys())
        print("  Force rebuild: all packages marked dirty")
    else:
        dirty: set[str] = set()
        # Check each package for direct changes since its baseline
        for name, info in packages.items():
            baseline = baselines.get(name)
            if not baseline:
                # First release for this package
                dirty.add(name)
                print(f"  {name}: new package")
                continue

            # Get files changed since this package's dev baseline
            changed_files = set(
                git("diff", "--name-only", baseline, "HEAD").splitlines()
            )

            # Filter to files in this package's directory
            prefix = info.path.rstrip("/") + "/"
            pkg_changed_files = {f for f in changed_files if f.startswith(prefix)}

            if pkg_changed_files:
                dirty.add(name)
                print(f"  {name}: changed since {baseline}")

            # Root config changes affect this package
            elif "pyproject.toml" in changed_files:
                dirty.add(name)
                print(f"  {name}: root config changed since {baseline}")

    # Build reverse dependency map
    reverse_deps: dict[str, list[str]] = {n: [] for n in packages}
    for name, info in packages.items():
        for dep in info.deps:
            reverse_deps[dep].append(name)

    # Propagate dirtiness to dependents using BFS
    queue = list(dirty)
    while queue:
        node = queue.pop(0)
        for dependent in reverse_deps[node]:
            if dependent not in dirty:
                print(f"  {dependent}: dirty (depends on {node})")
                dirty.add(dependent)
                queue.append(dependent)

    return list(dirty)
