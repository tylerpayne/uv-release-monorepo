"""Three-way merge command with optional editor for conflict resolution."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Literal

from .base import Command
from ..utils.merge import merge_texts


class MergeUpgradeCommand(Command):
    """Three-way merge of a file using git merge-file."""

    type: Literal["merge_upgrade"] = "merge_upgrade"
    file_path: str
    base_content: str
    incoming_content: str
    base_path: str = ""
    editor: str = ""

    def execute(self) -> int:
        if self.label:
            print(f"  {self.label}")
        current_path = Path(self.file_path)
        if not current_path.exists():
            current_path.parent.mkdir(parents=True, exist_ok=True)
            current_path.write_text(self.incoming_content)
            self._update_base()
            return 0
        current = current_path.read_text()
        merged, has_conflicts = merge_texts(
            current, self.base_content, self.incoming_content
        )
        if merged == current:
            print(f"    {self.file_path}: already up to date")
            return 0
        current_path.write_text(merged)
        self._update_base()
        if has_conflicts:
            return self._resolve_conflicts(current_path, current)
        return 0

    def _resolve_conflicts(self, path: Path, original: str) -> int:
        """Open editor for conflict resolution if configured."""
        if not self.editor:
            print(f"    {self.file_path}: merged with conflicts (resolve manually)")
            return 0
        try:
            answer = (
                input(f"    {self.file_path}: conflicts. Open in {self.editor}? [Y/n] ")
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if answer == "n":
            return 0
        subprocess.run([self.editor, str(path)])
        # Check if conflicts were resolved.
        content = path.read_text()
        if "<<<<<<< " in content:
            try:
                revert = (
                    input("    Unresolved conflicts. Revert? [Y/n] ").strip().lower()
                )
            except (EOFError, KeyboardInterrupt):
                print()
                return 1
            if revert != "n":
                path.write_text(original)
                print(f"    Reverted {self.file_path}")
            return 1
        print(f"    Conflicts resolved in {self.file_path}")
        return 0

    def _update_base(self) -> None:
        """Write the incoming content as the new merge base."""
        if self.base_path:
            p = Path(self.base_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(self.incoming_content)
