"""The ``uvr workflow runners`` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...shared.utils.cli import discover_package_names, fatal, print_matrix_status
from ...shared.utils.config import get_matrix, set_matrix
from ...shared.utils.toml import read_pyproject, write_pyproject
from .._args import CommandArgs

_DEFAULT_RUNNERS: list[list[str]] = [["ubuntu-latest"]]


class RunnersArgs(CommandArgs):
    """Typed arguments for ``uvr workflow runners``."""

    package: str | None = None
    add_value: str | None = None
    remove_value: str | None = None
    clear: bool = False


def cmd_runners(args: argparse.Namespace) -> None:
    """Manage per-package build runners in [tool.uvr.matrix]."""
    parsed = RunnersArgs.from_namespace(args)
    root = Path.cwd()
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        fatal("No pyproject.toml found in current directory.")

    doc = read_pyproject(pyproject)
    matrix = get_matrix(doc)

    pkg = parsed.package
    add_val = parsed.add_value
    remove_val = parsed.remove_value
    clear = parsed.clear

    # No package -> show all (fill in defaults for unconfigured packages)
    if not pkg:
        all_packages = discover_package_names()
        effective = {name: matrix.get(name, _DEFAULT_RUNNERS) for name in all_packages}
        print_matrix_status(effective)
        return

    # --clear
    if clear:
        if pkg in matrix:
            del matrix[pkg]
            set_matrix(doc, matrix)
            write_pyproject(pyproject, doc)
            print(f"Cleared runners for '{pkg}'.")
        else:
            print(f"'{pkg}' has no runners configured.")
        return

    # --add (comma-separated labels become a single runner)
    if add_val is not None:
        labels = [s.strip() for s in add_val.split(",")]
        runners = matrix.get(pkg, [])
        if labels in runners:
            print(f"'{add_val}' already in runners for '{pkg}'.")
            return
        runners.append(labels)
        matrix[pkg] = runners
        set_matrix(doc, matrix)
        write_pyproject(pyproject, doc)
        print(f"Added [{', '.join(labels)}] to '{pkg}' runners.")
        return

    # --remove
    if remove_val is not None:
        labels = [s.strip() for s in remove_val.split(",")]
        runners = matrix.get(pkg, [])
        if labels not in runners:
            fatal(f"[{', '.join(labels)}] not in runners for '{pkg}'")
        runners.remove(labels)
        if runners:
            matrix[pkg] = runners
        else:
            del matrix[pkg]
        set_matrix(doc, matrix)
        write_pyproject(pyproject, doc)
        print(f"Removed [{', '.join(labels)}] from '{pkg}' runners.")
        return

    # Read
    runners = matrix.get(pkg, _DEFAULT_RUNNERS)
    for r in runners:
        print(f"  [{', '.join(r)}]")
