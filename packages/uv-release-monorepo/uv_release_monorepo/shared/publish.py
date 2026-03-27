"""Publish: generate release notes for GitHub releases."""

from __future__ import annotations


from .models import PackageInfo
from .shell import git


def generate_release_notes(
    name: str,
    info: PackageInfo,
    baseline_tag: str | None,
) -> str:
    """Generate markdown release notes for a single package.

    Args:
        name: Package name.
        info: Package metadata (version, path).
        baseline_tag: Git tag to diff from (e.g. "pkg/v1.0.0"), or None.

    Returns:
        Markdown string with release header and commit log.
    """
    lines: list[str] = [f"**Released:** {name} {info.version}"]
    if baseline_tag:
        log = git(
            "log",
            "--oneline",
            f"{baseline_tag}..HEAD",
            "--",
            info.path,
            check=False,
        )
        if log:
            lines += ["", "**Commits:**"]
            for entry in log.splitlines()[:10]:
                lines.append(f"- {entry}")
    return "\n".join(lines)
