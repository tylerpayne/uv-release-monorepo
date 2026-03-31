"""CLI compatibility shim — re-exports from shared.utils.cli."""

from __future__ import annotations

from importlib.metadata import version as pkg_version

from ..shared.utils.cli import (
    diff_stat as _diff_stat,
    discover_package_names as _discover_package_names,
    discover_packages as _discover_packages,
    fatal as _fatal,
    parse_install_spec as _parse_install_spec,
    print_dependencies as _print_dependencies,
    print_matrix_status as _print_matrix_status,
    read_hooks as _read_hooks,
    read_matrix as _read_matrix,
    resolve_plan_json as _resolve_plan_json,
)

__version__ = pkg_version("uv-release-monorepo")

__all__ = [
    "__version__",
    "_diff_stat",
    "_discover_package_names",
    "_discover_packages",
    "_fatal",
    "_parse_install_spec",
    "_print_dependencies",
    "_print_matrix_status",
    "_read_hooks",
    "_read_matrix",
    "_resolve_plan_json",
]
