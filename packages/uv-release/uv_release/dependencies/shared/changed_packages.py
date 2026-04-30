"""ChangedPackages: which packages changed since their baselines."""

from __future__ import annotations

from collections import defaultdict

from diny import singleton, provider

from ...types.base import Frozen
from ...types.package import Package
from .baseline_tags import BaselineTags
from .git_repo import GitRepo
from ...types.version import VersionState
from .workspace_packages import WorkspacePackages


@singleton
class ChangedPackages(Frozen):
    """Package name -> reason it changed."""

    reasons: dict[str, str] = {}
    commit_logs: dict[str, str] = {}

    @property
    def names(self) -> frozenset[str]:
        return frozenset(self.reasons.keys())


@provider(ChangedPackages)
def provide_changed_packages(
    workspace_packages: WorkspacePackages,
    baseline_tags: BaselineTags,
    git_repo: GitRepo,
) -> ChangedPackages:
    # Phase 1: detect direct file changes. Missing baseline = initial release.
    head = git_repo.head_commit()
    packages = workspace_packages.items

    dirty: set[str] = set()
    reasons: dict[str, str] = {}
    commit_logs: dict[str, str] = {}

    for name, pkg in packages.items():
        baseline = baseline_tags.items.get(name)
        if baseline is None:
            dirty.add(name)
            reasons[name] = "initial release"
            continue
        if git_repo.path_changed(baseline.commit, head, pkg.path):
            dirty.add(name)
            reasons[name] = "files changed"
            commit_logs[name] = git_repo.commit_log(baseline.commit, head, pkg.path)

    # Phase 2: propagate through reverse deps.
    before_propagation = set(dirty)
    dirty = _propagate_dirtiness(dirty, packages)
    for name in dirty - before_propagation:
        reasons[name] = "dependency changed"

    sorted_dirty = sorted(dirty)
    return ChangedPackages(
        reasons={n: reasons[n] for n in sorted_dirty},
        commit_logs={n: commit_logs[n] for n in sorted_dirty if n in commit_logs},
    )


# Post-release versions don't propagate dirtiness to dependents.
_POST_RELEASE_STATES = frozenset(
    {
        VersionState.CLEAN_POST0,
        VersionState.CLEAN_POSTM,
        VersionState.DEV0_POST,
        VersionState.DEVK_POST,
    }
)


def _propagate_dirtiness(
    dirty: set[str],
    packages: dict[str, Package],
) -> set[str]:
    # BFS over reverse deps: if B is dirty, all consumers of B are too.
    if not dirty or not packages:
        return set(dirty)

    reverse_deps: dict[str, list[str]] = defaultdict(list)
    for name, pkg in packages.items():
        for dep in pkg.dep_names:
            if dep in packages:
                reverse_deps[dep].append(name)

    result = set(dirty)
    queue = list(dirty)
    while queue:
        current = queue.pop(0)
        pkg = packages.get(current)
        if pkg is None:
            continue
        if pkg.version.state in _POST_RELEASE_STATES:
            continue
        for dependent in reverse_deps.get(current, []):
            if dependent not in result:
                result.add(dependent)
                queue.append(dependent)

    return result
