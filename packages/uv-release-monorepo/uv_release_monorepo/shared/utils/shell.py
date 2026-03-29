"""Shell utilities: output formatting, progress, and error helpers."""

from __future__ import annotations

import sys
import time


def print_step(msg: str) -> None:
    """Print a visually distinct step header.

    Used to separate major phases of the release pipeline in terminal output.
    """
    print(f"\n{'─' * 60}\n{msg}\n{'─' * 60}")


def exit_fatal(msg: str) -> None:
    """Print an error message and exit with code 1.

    Use for unrecoverable errors that should halt the pipeline.
    """
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


_SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class Progress:
    """ASCII progress reporter with spinner.

    While running, shows a spinner + current step on stderr.
    On finish, prints a detailed summary with per-phase timing to stdout.
    """

    def __init__(self) -> None:
        self._start = time.monotonic()
        self._step_start = self._start
        self._completed: list[tuple[str, int]] = []
        self._spin_idx = 0

    def update(self, msg: str) -> None:
        """Show a spinner with the current step message."""
        frame = _SPINNER[self._spin_idx % len(_SPINNER)]
        self._spin_idx += 1
        sys.stderr.write(f"\r  {frame} {msg}...".ljust(60))
        sys.stderr.flush()
        self._step_start = time.monotonic()

    def complete(self, summary: str) -> None:
        """Record a completed step with its summary text and elapsed time."""
        elapsed_ms = int((time.monotonic() - self._step_start) * 1000)
        self._completed.append((summary, elapsed_ms))
        # Show checkmark briefly
        sys.stderr.write(f"\r  ✓ {summary} ({elapsed_ms}ms)".ljust(60))
        sys.stderr.flush()
        self._step_start = time.monotonic()

    def finish(self) -> None:
        """Clear the progress line and print the detailed summary."""
        total_ms = int((time.monotonic() - self._start) * 1000)
        sys.stderr.write("\r" + " " * 60 + "\r")
        sys.stderr.flush()
        for summary, ms in self._completed:
            print(f"  {summary} ({ms}ms)")
        print(f"  Resolved in {total_ms}ms")
