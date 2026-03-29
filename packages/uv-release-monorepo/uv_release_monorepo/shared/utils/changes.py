"""Change detection: determine which packages need rebuilding."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

import pygit2

from ..models import PackageInfo
from .shell import print_step

from ..planner._graph import build_graph_maps

if TYPE_CHECKING:
    from ..context import RepositoryContext


def _resolve_commit(repo: pygit2.Repository, tag_name: str) -> pygit2.Commit | None:
    """Resolve a tag name to its underlying commit object."""
    tag_ref = repo.references.get(f"refs/tags/{tag_name}")
    if tag_ref is None:
        return None
    target = repo.get(tag_ref.target)
    if isinstance(target, pygit2.Tag):
        target = repo.get(target.target)
    return target  # type: ignore[return-value]


def _path_changed(
    repo: pygit2.Repository,
    old_commit: pygit2.Commit,
    new_commit: pygit2.Commit,
    path: str,
) -> bool:
    """Check if any files under *path* differ between two commits.

    Compares subtrees directly — O(files in path), not O(files in repo).
    """
    prefix = path.rstrip("/") + "/"
    parts = prefix.rstrip("/").split("/")

    # Walk the tree path to find the subtree entry
    old_tree = old_commit.peel(pygit2.Tree)
    new_tree = new_commit.peel(pygit2.Tree)

    for part in parts:
        try:
            old_entry = old_tree[part] if old_tree else None  # type: ignore[index]
        except KeyError:
            old_entry = None
        try:
            new_entry = new_tree[part] if new_tree else None  # type: ignore[index]
        except KeyError:
            new_entry = None

        if old_entry is None and new_entry is None:
            return False  # path doesn't exist in either
        if old_entry is None or new_entry is None:
            return True  # path exists in one but not the other

        # Same OID → identical subtree, no changes
        if old_entry.id == new_entry.id:
            return False

        old_tree = repo.get(old_entry.id)
        new_tree = repo.get(new_entry.id)

    # Subtrees differ — something changed under this path
    return True


def detect_changes(
    packages: dict[str, PackageInfo],
    baselines: Mapping[str, str | None],
    rebuild_all: bool,
    *,
    ctx: RepositoryContext | None = None,
    repo: pygit2.Repository | None = None,
) -> list[str]:
    """Determine which packages need to be rebuilt.

    A package is "dirty" and needs rebuilding if:
    1. rebuild_all is True (rebuild everything)
    2. No previous baseline tag exists for the package (first release)
    3. Any file in the package directory changed since its baseline
    4. Any of its dependencies are dirty (transitive dirtiness)

    Uses subtree comparison for O(depth) per package instead of full repo
    diffs. Caches baseline commit resolution to avoid redundant work when
    multiple packages share the same baseline tag.

    Args:
        packages: Map of package name -> PackageInfo.
        baselines: Map of package name -> baseline tag (or None).
        rebuild_all: If True, mark all packages as dirty.
        ctx: RepositoryContext providing the repo. Preferred over *repo*.
        repo: Pre-opened pygit2 Repository. Opened automatically if None.

    Returns:
        List of changed package names.
    """
    print_step("Detecting changes")

    if ctx is not None:
        repo = ctx.repo
    elif repo is None:
        from .git import open_repo

        repo = open_repo()

    if rebuild_all:
        dirty = set(packages.keys())
        print("  Force rebuild: all packages marked dirty")
    else:
        dirty: set[str] = set()

        # Packages without baselines are automatically dirty (first release)
        to_check: list[tuple[str, PackageInfo, str]] = []
        for name, info in packages.items():
            baseline = baselines.get(name)
            if not baseline:
                dirty.add(name)
                print(f"  {name}: new package")
            else:
                to_check.append((name, info, baseline))

        # Cache baseline commit lookups — multiple packages may share a baseline
        commit_cache: dict[str, pygit2.Commit | None] = {}
        head = repo.revparse_single("HEAD")

        for name, info, baseline in to_check:
            if baseline not in commit_cache:
                commit_cache[baseline] = _resolve_commit(repo, baseline)

            base_commit = commit_cache[baseline]
            if base_commit is None:
                dirty.add(name)
                print(f"  {name}: baseline tag missing ({baseline})")
                continue

            if _path_changed(repo, base_commit, head, info.path):  # type: ignore[arg-type]
                dirty.add(name)
                print(f"  {name}: changed since {baseline}")

    # Build reverse dependency map
    _, reverse_deps = build_graph_maps(packages)

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
