from __future__ import annotations

from pathlib import Path

import diny
import pytest

from conftest import run_cli


class TestSkillUpgrade:
    def test_scaffolds_skill_files(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with diny.provide():
            run_cli("skill", "install")
        out = capsys.readouterr().out
        assert "Create" in out or "skill-upgrade" in out
        # Skill files should now exist in the workspace.
        skills_dir = workspace / ".claude" / "skills"
        assert skills_dir.exists()
