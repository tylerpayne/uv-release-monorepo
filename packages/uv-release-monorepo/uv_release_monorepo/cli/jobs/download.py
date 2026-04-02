"""The ``uvr jobs download`` command."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from packaging.utils import canonicalize_name

from ...shared.models import DownloadWheelsCommand, ReleasePlan
from ...shared.utils.cli import resolve_plan_json
from .._args import CommandArgs


class JobDownloadArgs(CommandArgs):
    """Typed arguments for ``uvr jobs download``."""

    plan: str | None = None


def cmd_download(args: argparse.Namespace) -> None:
    """Download wheels for all changed packages into dist/."""
    parsed = JobDownloadArgs.from_namespace(args)
    plan_obj = ReleasePlan.model_validate_json(resolve_plan_json(parsed.plan))

    # Check if wheels already exist locally (e.g. local build)
    dist = Path("dist")
    if dist.is_dir():
        all_present = True
        for name, pkg in plan_obj.changed.items():
            dist_name = canonicalize_name(name).replace("-", "_")
            pattern = f"{dist_name}-{pkg.release_version}-*.whl"
            if not list(dist.glob(pattern)):
                all_present = False
                break
        if all_present:
            print("All wheels already in dist/, skipping download.")
            return

    # Use reuse_run_id if set, otherwise fall back to current run
    run_id = plan_obj.reuse_run_id or os.environ.get("GITHUB_RUN_ID")
    if not run_id:
        print(
            "ERROR: No run ID and wheels not in dist/. "
            "Set --reuse-run or run in GitHub Actions.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Build the packages dict: name -> release tag (for fallback)
    packages = {
        name: f"{name}/v{pkg.release_version}" for name, pkg in plan_obj.changed.items()
    }

    cmd = DownloadWheelsCommand(
        packages=packages,
        run_id=run_id,
        all_platforms=True,
        directory="dist",
        label="Download release wheels",
    )
    result = cmd.execute()
    if result.returncode != 0:
        print("ERROR: Failed to download wheels.", file=sys.stderr)
        sys.exit(1)
