"""Display and formatting for CLI output."""

from __future__ import annotations

from ..types import Plan


def format_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> list[str]:
    """Format rows into aligned columns. Returns lines without trailing newlines."""
    if not rows:
        return []
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    lines: list[str] = []
    lines.append("  " + "  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    for row in rows:
        lines.append("  " + "  ".join(cell.ljust(w) for cell, w in zip(row, widths)))
    return lines


def print_plan_summary(plan: Plan) -> None:
    """Print the release plan summary including packages and pipeline."""
    if not plan.jobs:
        return

    if plan.releases:
        print("Packages")
        print("--------")
        headers = ("PACKAGE", "CURRENT", "RELEASE", "NEXT", "DIFF FROM")
        rows = [
            (
                name,
                release.package.version.raw,
                release.release_version.raw,
                release.next_version.raw,
                release.baseline_tag or "(initial)",
            )
            for name, release in sorted(plan.releases.items())
        ]
        for line in format_table(headers, rows):
            print(line)
        print()

    print("Pipeline")
    print("--------")
    skipped = set(plan.skip)
    for job in plan.jobs:
        status = "skip" if job.name in skipped else "run"
        print(f"  {status.ljust(6)}  {job.name}")


def print_bump_summary(results: list[tuple[str, str, str]]) -> None:
    """Print a before/after version table for bump results."""
    if not results:
        return
    nw = max(len(name) for name, _, _ in results)
    ow = max(len(old) for _, old, _ in results)
    for name, old, new in results:
        print(f"  {name.ljust(nw)}  {old.ljust(ow)}  ->  {new}")
