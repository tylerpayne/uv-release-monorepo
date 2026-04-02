"""The ``uvr download`` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from packaging.utils import canonicalize_name

from ._args import CommandArgs
from ..shared.utils.cli import fatal, parse_install_spec, resolve_gh_repo
from ..shared.utils.tags import find_latest_remote_release_tag


class DownloadArgs(CommandArgs):
    """Typed arguments for ``uvr download``."""

    output: str = "dist"
    run_id: str | None = None
    package: str | None = None
    release_tag: str | None = None
    repo: str | None = None
    all_platforms: bool = False


def cmd_download(args: argparse.Namespace) -> None:
    """Download platform-compatible wheels from a GitHub release or CI run."""
    from ..shared.models import FetchGithubReleaseCommand, FetchRunArtifactsCommand

    parsed = DownloadArgs.from_namespace(args)

    output_dir: str = parsed.output
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if parsed.run_id:
        # --run-id: download all wheels from the run's artifacts.
        # package is optional — used to filter if provided.
        if parsed.package:
            _, package, _ = parse_install_spec(parsed.package)
            dist_name = canonicalize_name(package).replace("-", "_")
        else:
            package = None
            dist_name = ""  # empty prefix matches all wheels

        from ..shared.utils.cli import infer_gh_repo

        gh_repo = parsed.repo or infer_gh_repo() or ""

        cmd = FetchRunArtifactsCommand(
            run_id=parsed.run_id,
            dist_name=dist_name,
            gh_repo=gh_repo,
            all_platforms=parsed.all_platforms,
            directory=output_dir,
            label=f"Fetch wheels from run {parsed.run_id}",
        )
    else:
        if not parsed.package:
            fatal("Package name required (e.g. my-pkg or my-pkg@1.0.0).")
        spec_repo, package, version = parse_install_spec(parsed.package)
        gh_repo = resolve_gh_repo(parsed.repo, spec_repo)
        dist_name = canonicalize_name(package).replace("-", "_")

        if parsed.release_tag:
            tag = parsed.release_tag
        elif version:
            tag = f"{package}/v{version}"
        else:
            tag = find_latest_remote_release_tag(package, gh_repo=gh_repo)
        if not tag:
            fatal(f"No release found for '{package}'.")

        cmd = FetchGithubReleaseCommand(
            tag=tag,
            dist_name=dist_name,
            gh_repo=gh_repo,
            directory=output_dir,
            label=f"Fetch {package} from {tag}",
        )

    result = cmd.execute()
    if result.returncode != 0:
        label = package or f"run {parsed.run_id}"
        fatal(f"Download failed for '{label}'. See errors above.")

    glob_pattern = f"{dist_name}-*.whl" if dist_name else "*.whl"
    found = list(Path(output_dir).glob(glob_pattern))
    for whl in found:
        print(f"  {whl.name}")
    print(f"\nSaved {len(found)} wheel(s) to {output_dir}/")
