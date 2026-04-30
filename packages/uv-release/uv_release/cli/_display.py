"""Display and formatting for CLI output."""

from __future__ import annotations


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
