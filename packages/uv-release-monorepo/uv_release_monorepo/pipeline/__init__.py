"""Release pipeline: discover -> diff -> build -> publish -> tag -> bump.

This package orchestrates the uv-release-monorepo release process:
1. Discover all packages in the workspace
2. Detect which packages changed since last release
3. Fetch unchanged wheels from previous release (avoid rebuilding)
4. Build only the changed packages
5. Publish wheels to GitHub Releases
6. Tag released packages (only after successful publish)
7. Bump versions for next development cycle
8. Push tags and version bump commit back to main

The key optimization is that unchanged packages are not rebuilt - their
wheels are reused from the previous release. Tagging and bumping happen
only after a successful publish, so a failed release leaves no artifacts.
"""

from __future__ import annotations

from pathlib import Path

# Re-export shell utilities so mock.patch("uv_release_monorepo.pipeline.git") still works
from ..deps import rewrite_pyproject
from ..shell import fatal, gh, git, run, step

# Re-export all public functions from submodules
from .build import build_packages, fetch_unchanged_wheels
from .bumps import bump_versions, collect_published_state, commit_bumps
from .changes import check_for_existing_wheels, detect_changes, get_existing_wheels
from .discovery import discover_packages, find_release_tags, get_baseline_tags
from .execute import execute_plan, run_release
from .plan import apply_bumps, build_plan, write_dep_pins
from .publish import generate_release_notes, publish_release
from .tags import tag_baselines, tag_changed_packages

__all__ = [
    # Standard library (re-exported for mock compatibility)
    "Path",
    # Shell utilities (re-exported for mock compatibility)
    "fatal",
    "gh",
    "git",
    "rewrite_pyproject",
    "run",
    "step",
    # Discovery
    "discover_packages",
    "find_release_tags",
    "get_baseline_tags",
    # Changes
    "check_for_existing_wheels",
    "detect_changes",
    "get_existing_wheels",
    # Build
    "build_packages",
    "fetch_unchanged_wheels",
    # Tags
    "tag_baselines",
    "tag_changed_packages",
    # Bumps
    "bump_versions",
    "collect_published_state",
    "commit_bumps",
    # Publish
    "generate_release_notes",
    "publish_release",
    # Plan
    "apply_bumps",
    "build_plan",
    "write_dep_pins",
    # Execute
    "execute_plan",
    "run_release",
]
