"""Helpers for script-based GitHub Actions workflow steps."""

from __future__ import annotations

import argparse
import sys

from .models import ReleasePlan
from .pipeline import (
    apply_bumps,
    build_packages,
    commit_bumps,
    fetch_unchanged_wheels,
    publish_release,
    run_release,
    tag_changed_packages,
    tag_dev_baselines,
)
from .shell import git


def run_pipeline(force_all: bool, push: bool = True, dry_run: bool = False) -> None:
    """Run the full release pipeline."""
    run_release(force_all=force_all, push=push, dry_run=dry_run)


def execute_prepare_release(plan_json: str, package: str) -> None:
    """CI step: strip .dev0 from a package's version before building."""
    from pathlib import Path

    from .deps import rewrite_pyproject
    from .versions import strip_dev

    plan = ReleasePlan.model_validate_json(plan_json)
    if package not in plan.changed:
        return
    info = plan.changed[package]
    # The plan stores the clean release version (already stripped).
    # Write it to pyproject.toml in case the checked-out file has .dev0.
    rewrite_pyproject(
        Path(info.path) / "pyproject.toml",
        strip_dev(info.version),
        {},
    )


def execute_build(plan_json: str, package: str) -> None:
    """CI build step: build one package if it is in the plan's changed set."""
    plan = ReleasePlan.model_validate_json(plan_json)
    if package not in plan.changed:
        print(f"  {package} not in changed list, skipping")
        return
    build_packages({package: plan.changed[package]})


def execute_fetch_unchanged(plan_json: str) -> None:
    """CI step: download wheels for unchanged packages from their GitHub releases."""
    plan = ReleasePlan.model_validate_json(plan_json)
    fetch_unchanged_wheels(plan.unchanged, plan.release_tags)


def execute_publish_releases(plan_json: str) -> None:
    """CI step: create one GitHub release per changed package."""
    plan = ReleasePlan.model_validate_json(plan_json)
    publish_release(plan.changed, plan.release_tags)


def execute_finalize(plan_json: str) -> None:
    """CI step: tag packages, apply pre-computed bumps, commit, tag dev baselines, push.

    Behavior is driven entirely by the plan:
    - ``ci_publish=True``: skip release tag creation (the publish action already
      created them), configure git identity, and push at the end.
    - ``ci_publish=False``: create release tags locally (default for local execution).
    """
    plan = ReleasePlan.model_validate_json(plan_json)
    if plan.ci_publish:
        git("config", "user.name", "github-actions[bot]")
        git("config", "user.email", "github-actions[bot]@users.noreply.github.com")
    if not plan.ci_publish:
        tag_changed_packages(plan.changed)
    bumped = apply_bumps(plan)
    commit_bumps(plan.changed, bumped)
    tag_dev_baselines(bumped)
    if plan.ci_publish:
        git("push")
        git("push", "--tags")


def execute_release(plan_json: str) -> None:
    """Run all release steps in sequence (convenience wrapper for local use)."""
    execute_fetch_unchanged(plan_json)
    execute_publish_releases(plan_json)
    execute_finalize(plan_json)


def main(argv: list[str] | None = None) -> None:
    """Run a workflow step command."""
    args = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="python -m uv_release_monorepo.workflow_steps"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    execute_build_parser = subparsers.add_parser("execute-build")
    execute_build_parser.add_argument(
        "--plan", required=True, help="Release plan JSON."
    )
    execute_build_parser.add_argument(
        "--package", required=True, help="Package name to build."
    )

    prepare_release_parser = subparsers.add_parser("prepare-release")
    prepare_release_parser.add_argument(
        "--plan", required=True, help="Release plan JSON."
    )
    prepare_release_parser.add_argument(
        "--package", required=True, help="Package name to prepare."
    )

    execute_release_parser = subparsers.add_parser("execute-release")
    execute_release_parser.add_argument(
        "--plan", required=True, help="Release plan JSON."
    )

    fetch_unchanged_parser = subparsers.add_parser("fetch-unchanged")
    fetch_unchanged_parser.add_argument(
        "--plan", required=True, help="Release plan JSON."
    )

    publish_releases_parser = subparsers.add_parser("publish-releases")
    publish_releases_parser.add_argument(
        "--plan", required=True, help="Release plan JSON."
    )

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--plan", required=True, help="Release plan JSON.")

    parsed = parser.parse_args(args)
    if parsed.command == "execute-build":
        execute_build(parsed.plan, parsed.package)
    elif parsed.command == "prepare-release":
        execute_prepare_release(parsed.plan, parsed.package)
    elif parsed.command == "execute-release":
        execute_release(parsed.plan)
    elif parsed.command == "fetch-unchanged":
        execute_fetch_unchanged(parsed.plan)
    elif parsed.command == "publish-releases":
        execute_publish_releases(parsed.plan)
    elif parsed.command == "finalize":
        execute_finalize(parsed.plan)


if __name__ == "__main__":
    main()
