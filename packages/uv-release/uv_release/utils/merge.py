"""Three-way merge via git merge-file. Pure function, no DI."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def merge_texts(current: str, base: str, incoming: str) -> tuple[str, bool]:
    """Three-way merge of three text strings.

    Returns (merged_text, has_conflicts). Uses git merge-file under the hood.
    """
    with (
        tempfile.NamedTemporaryFile(mode="w", suffix=".current", delete=False) as f_cur,
        tempfile.NamedTemporaryFile(mode="w", suffix=".base", delete=False) as f_base,
        tempfile.NamedTemporaryFile(
            mode="w", suffix=".incoming", delete=False
        ) as f_inc,
    ):
        f_cur.write(current)
        f_base.write(base)
        f_inc.write(incoming)
        f_cur.flush()
        f_base.flush()
        f_inc.flush()

        result = subprocess.run(
            [
                "git",
                "merge-file",
                "-p",
                "-L",
                "current",
                "-L",
                "base",
                "-L",
                "incoming",
                f_cur.name,
                f_base.name,
                f_inc.name,
            ],
            capture_output=True,
            text=True,
        )

    for p in [f_cur.name, f_base.name, f_inc.name]:
        Path(p).unlink(missing_ok=True)

    return result.stdout, result.returncode > 0
