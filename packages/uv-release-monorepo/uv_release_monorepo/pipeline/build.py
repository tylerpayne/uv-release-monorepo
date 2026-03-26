"""Build: fetch unchanged wheels and build changed packages."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from packaging.utils import canonicalize_name


from ..graph import topo_sort
from ..models import PackageInfo
from ..shell import fatal, run, step


def fetch_unchanged_wheels(
    unchanged: dict[str, PackageInfo],
    release_tags: Mapping[str, str | None],
) -> None:
    """Download wheels for unchanged packages from their per-package GitHub releases.

    Each package has its own GitHub release tagged {package}/v{version}. This
    function downloads the wheel for each unchanged package directly from its
    release, avoiding a full scan of all releases.

    Args:
        unchanged: Map of unchanged package names to PackageInfo.
        release_tags: Map of package name to last release tag (e.g. "pkg/v1.2.3").
    """
    if not unchanged:
        return

    step("Fetching unchanged wheels from releases")

    for name in unchanged:
        tag = release_tags.get(name)
        if not tag:
            # TODO: Real warning
            print(f"  Warning: no release tag for {name}, skipping")
            continue

        wheel_name = canonicalize_name(name).replace("-", "_")
        result = run(
            "gh",
            "release",
            "download",
            tag,
            "--pattern",
            f"{wheel_name}-*.whl",
            "--dir",
            "dist/",
            "--clobber",
            check=False,
        )
        if result.returncode != 0:
            print(f"  Warning: could not download wheel for {name} from {tag}")
            continue

        # Find what was downloaded and report it
        released_version = tag.split("/v")[-1] if "/v" in tag else ""
        found = list(Path("dist").glob(f"{wheel_name}-{released_version}-*.whl"))
        if found:
            print(f"  Reusing: {found[0].name}")
        else:
            # TODO: Real warning
            print(f"  Warning: no wheel found for {name} after downloading {tag}")


def build_packages(changed: dict[str, PackageInfo]) -> None:
    """Build wheels for the specified packages using uv build.

    Packages are built in topological order so dependencies are built
    before the packages that depend on them.
    """
    step(f"Building {len(changed)} packages")

    # Build in dependency order
    # TODO: shouldn't this be topo_layers? with parallel builds per layer?
    build_order = topo_sort(changed)
    for pkg in build_order:
        info = changed[pkg]
        print(f"\n  {pkg} ({info.path})")
        result = run(
            "uv",
            "build",
            info.path,
            "--out-dir",
            "dist/",
            "--find-links",
            "dist/",
            check=False,
        )
        if result.returncode != 0:
            fatal(f"Failed to build {pkg}. Check uv build output above for details.")
