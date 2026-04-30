"""Git repository singleton. All git I/O goes through this."""

from __future__ import annotations

import subprocess

import pygit2
from diny import singleton
from packaging.version import InvalidVersion
from packaging.version import Version as PkgVersion

from ...types.tag import Tag
from ...types.version import Version


@singleton
class GitRepo:
    """All git I/O goes through this class."""

    _repo: pygit2.Repository

    def __init__(self) -> None:
        self._repo = pygit2.Repository(".")

    def find_tag(self, tag_name: str) -> str | None:
        ref = f"refs/tags/{tag_name}"
        if self._repo.references.get(ref) is None:
            return None
        try:
            return str(self._repo.revparse_single(ref).id)
        except (KeyError, AttributeError, pygit2.GitError):
            return None

    def list_tags(self, prefix: str) -> list[str]:
        full_prefix = f"refs/tags/{prefix}"
        result: list[str] = []
        try:
            for ref in self._repo.listall_references():
                if ref.startswith(full_prefix):
                    result.append(ref[len("refs/tags/") :])
        except (AttributeError, OSError):
            pass
        return result

    def path_changed(self, from_commit: str, to_commit: str, path: str) -> bool:
        try:
            from_tree = self._repo.revparse_single(from_commit).peel(pygit2.Tree)
            to_tree = self._repo.revparse_single(to_commit).peel(pygit2.Tree)
        except (KeyError, AttributeError):
            return True
        try:
            from_oid = from_tree[path].id
        except KeyError:
            return True
        try:
            to_oid = to_tree[path].id
        except KeyError:
            return True
        return from_oid != to_oid

    def commit_log(self, from_commit: str, to_commit: str, path: str) -> str:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", f"{from_commit}..{to_commit}", "--", path],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            return ""

    def head_commit(self) -> str:
        return str(self._repo.revparse_single("HEAD").id)

    def is_dirty(self) -> bool:
        status = self._repo.status()
        return len(status) > 0

    def file_is_dirty(self, path: str) -> bool:
        """Check if a specific file has uncommitted changes."""
        try:
            result = subprocess.run(
                ["git", "diff", "--quiet", "--", path],
                capture_output=True,
            )
            return result.returncode != 0
        except (OSError, subprocess.SubprocessError):
            return False

    def is_ahead_or_behind(self) -> bool:
        head = self._repo.head
        branch = self._repo.branches.get(head.shorthand)
        if branch is None:
            return False
        upstream = branch.upstream
        if upstream is None:
            return False
        return branch.target != upstream.target

    # --- Tag query methods ---

    def find_release_tags(self, name: str) -> list[tuple[PkgVersion, str]]:
        """All non-baseline release tags for a package, sorted highest first."""
        prefix = Tag.tag_prefix(name)
        candidates: list[tuple[PkgVersion, str]] = []
        for tag_name in self.list_tags(prefix):
            if Tag.is_baseline_tag_name(tag_name):
                continue
            ver_str = tag_name[len(prefix) :]
            try:
                pv = PkgVersion(ver_str)
            except InvalidVersion:
                continue
            candidates.append((pv, tag_name))
        candidates.sort(reverse=True)
        return candidates

    def find_latest_release_tag(self, name: str) -> str | None:
        """Find the highest version release tag for a package."""
        candidates = self.find_release_tags(name)
        return candidates[0][1] if candidates else None

    def find_previous_release_tag(self, name: str, below: PkgVersion) -> str | None:
        """Find the highest release tag below a given version."""
        candidates = self.find_release_tags(name)
        for pv, tag_name in candidates:
            if pv < below:
                return tag_name
        return None

    def resolve_tag(
        self, package_name: str, tag_name: str, *, is_baseline: bool
    ) -> Tag | None:
        """Resolve a tag name to a Tag with its commit SHA. None if tag missing."""
        commit = self.find_tag(tag_name)
        if commit is None:
            return None
        ver_str = Tag.parse_version_from_tag_name(tag_name)
        return Tag(
            package_name=package_name,
            raw=tag_name,
            version=Version.parse(ver_str),
            is_baseline=is_baseline,
            commit=commit,
        )
