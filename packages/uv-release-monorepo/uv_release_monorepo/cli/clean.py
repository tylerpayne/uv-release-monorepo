"""The ``uvr clean`` command."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def cmd_clean(args: argparse.Namespace) -> None:
    """Remove uvr caches and ephemeral files."""
    removed: list[str] = []

    # ~/.uvr/cache (download cache)
    home_cache = Path.home() / ".uvr" / "cache"
    if home_cache.is_dir():
        shutil.rmtree(home_cache)
        removed.append(str(home_cache))

    # .uvr/ in the current project (release notes, bases, etc.)
    local_uvr = Path.cwd() / ".uvr"
    if local_uvr.is_dir():
        for subdir in ("cache", "release-notes"):
            target = local_uvr / subdir
            if target.is_dir():
                shutil.rmtree(target)
                removed.append(str(target))

    if removed:
        for p in removed:
            print(f"  removed {p}")
        print(f"\nCleaned {len(removed)} location(s).")
    else:
        print("Nothing to clean.")
