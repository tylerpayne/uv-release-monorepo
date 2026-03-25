"""Tests for YAML helpers and the workflow command."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from uv_release_monorepo.cli import (
    _MISSING,
    _yaml_delete,
    _yaml_get,
    _yaml_set,
    cmd_workflow,
)

from tests._helpers import _init_workflow, _wf_args


# ---------------------------------------------------------------------------
# YAML helpers: _yaml_get, _yaml_set, _yaml_delete
# ---------------------------------------------------------------------------


class TestYamlGet:
    def test_shallow(self) -> None:
        assert _yaml_get({"a": 1}, ["a"]) == 1

    def test_nested(self) -> None:
        assert _yaml_get({"a": {"b": {"c": 3}}}, ["a", "b", "c"]) == 3

    def test_missing_key(self) -> None:
        assert _yaml_get({"a": 1}, ["b"]) is _MISSING

    def test_missing_nested(self) -> None:
        assert _yaml_get({"a": {"b": 1}}, ["a", "x"]) is _MISSING

    def test_empty_path(self) -> None:
        doc = {"a": 1}
        assert _yaml_get(doc, []) is doc

    def test_returns_dict(self) -> None:
        assert _yaml_get({"a": {"b": 1}}, ["a"]) == {"b": 1}

    def test_returns_list(self) -> None:
        assert _yaml_get({"a": [1, 2]}, ["a"]) == [1, 2]

    def test_list_index(self) -> None:
        assert _yaml_get({"a": [10, 20, 30]}, ["a", "1"]) == 20

    def test_list_index_nested(self) -> None:
        doc = {"steps": [{"name": "first"}, {"name": "second"}]}
        assert _yaml_get(doc, ["steps", "0", "name"]) == "first"

    def test_list_index_out_of_range(self) -> None:
        assert _yaml_get({"a": [1]}, ["a", "5"]) is _MISSING


class TestYamlSet:
    def test_shallow(self) -> None:
        doc: dict = {}
        _yaml_set(doc, ["a"], 1)
        assert doc == {"a": 1}

    def test_nested_creates_intermediates(self) -> None:
        doc: dict = {}
        _yaml_set(doc, ["a", "b", "c"], 3)
        assert doc == {"a": {"b": {"c": 3}}}

    def test_overwrites_existing(self) -> None:
        doc = {"a": 1}
        _yaml_set(doc, ["a"], 2)
        assert doc == {"a": 2}

    def test_deep_overwrite(self) -> None:
        doc = {"a": {"b": {"c": "old"}}}
        _yaml_set(doc, ["a", "b", "c"], "new")
        assert doc["a"]["b"]["c"] == "new"

    def test_creates_intermediate_over_non_dict(self) -> None:
        doc = {"a": "scalar"}
        _yaml_set(doc, ["a", "b"], 1)
        assert doc == {"a": {"b": 1}}

    def test_set_list(self) -> None:
        doc: dict = {}
        _yaml_set(doc, ["items"], [1, 2, 3])
        assert doc == {"items": [1, 2, 3]}

    def test_set_list_element(self) -> None:
        doc = {"items": [10, 20, 30]}
        _yaml_set(doc, ["items", "1"], 99)
        assert doc["items"] == [10, 99, 30]


class TestYamlDelete:
    def test_shallow(self) -> None:
        doc = {"a": 1, "b": 2}
        assert _yaml_delete(doc, ["a"]) is True
        assert doc == {"b": 2}

    def test_nested(self) -> None:
        doc = {"a": {"b": 1, "c": 2}}
        assert _yaml_delete(doc, ["a", "b"]) is True
        assert doc == {"a": {"c": 2}}

    def test_missing_returns_false(self) -> None:
        doc = {"a": 1}
        assert _yaml_delete(doc, ["b"]) is False
        assert doc == {"a": 1}

    def test_missing_nested_returns_false(self) -> None:
        doc = {"a": {"b": 1}}
        assert _yaml_delete(doc, ["a", "x"]) is False

    def test_missing_parent_returns_false(self) -> None:
        doc = {"a": 1}
        assert _yaml_delete(doc, ["x", "y"]) is False

    def test_delete_list_element(self) -> None:
        doc = {"items": [10, 20, 30]}
        assert _yaml_delete(doc, ["items", "1"]) is True
        assert doc["items"] == [10, 30]


# ---------------------------------------------------------------------------
# cmd_workflow integration tests (new CRUD syntax with dot paths)
# ---------------------------------------------------------------------------


class TestCmdWorkflowRead:
    def test_read_permissions(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".permissions"))
        out = capsys.readouterr().out
        assert "contents" in out

    def test_read_missing_key(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".nonexistent"))
        out = capsys.readouterr().out
        assert "not found" in out

    def test_read_no_path_dumps_doc(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        capsys.readouterr()
        cmd_workflow(_wf_args())
        out = capsys.readouterr().out
        assert "jobs:" in out


class TestCmdWorkflowSet:
    def test_set_scalar(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".permissions.id-token", set_value="write"))
        cmd_workflow(_wf_args(path=".permissions.id-token"))
        out = capsys.readouterr().out
        assert "write" in out

    def test_set_creates_intermediates(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".jobs.build.environment", set_value="prod"))
        cmd_workflow(_wf_args(path=".jobs.build.environment"))
        out = capsys.readouterr().out
        assert "prod" in out

    def test_set_rejects_invalid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        with pytest.raises(SystemExit):
            cmd_workflow(_wf_args(path=".jobs.bogus", set_value="{runs-on: ubuntu}"))


class TestCmdWorkflowClear:
    def test_clear_existing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".permissions.id-token", set_value="write"))
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".permissions.id-token", clear=True))
        out = capsys.readouterr().out
        assert "Cleared" in out

    def test_clear_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".permissions.nope", clear=True))
        out = capsys.readouterr().out
        assert "not found" in out

    def test_clear_empties_dict(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """--clear on a dict should empty it, not delete the key."""
        release_yml = _init_workflow(tmp_path, monkeypatch)
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".permissions", clear=True))
        out = capsys.readouterr().out
        assert "Cleared" in out
        doc = yaml.safe_load(release_yml.read_text())
        # Key should still exist but be empty
        assert doc["permissions"] == {} or doc.get("permissions") is None


class TestCmdWorkflowList:
    def test_append_creates_list(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="release"))
        cmd_workflow(_wf_args(path=".jobs.build.tags"))
        out = capsys.readouterr().out
        assert "release" in out

    def test_append_appends(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        release_yml = _init_workflow(tmp_path, monkeypatch)
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="a"))
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="b"))
        doc = yaml.safe_load(release_yml.read_text())
        assert doc["jobs"]["build"]["tags"] == ["a", "b"]

    def test_append_to_non_list_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        with pytest.raises(SystemExit):
            cmd_workflow(_wf_args(path=".permissions.contents", append_value="read"))

    def test_insert_at_index(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        release_yml = _init_workflow(tmp_path, monkeypatch)
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="a"))
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="c"))
        cmd_workflow(_wf_args(path=".jobs.build.tags", insert_value="b", at_index=1))
        doc = yaml.safe_load(release_yml.read_text())
        assert doc["jobs"]["build"]["tags"] == ["a", "b", "c"]

    def test_insert_requires_at(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="a"))
        with pytest.raises(SystemExit):
            cmd_workflow(_wf_args(path=".jobs.build.tags", insert_value="b"))

    def test_remove_value(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        release_yml = _init_workflow(tmp_path, monkeypatch)
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="a"))
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="b"))
        cmd_workflow(_wf_args(path=".jobs.build.tags", remove_value="a"))
        doc = yaml.safe_load(release_yml.read_text())
        assert doc["jobs"]["build"]["tags"] == ["b"]

    def test_remove_missing_value_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="a"))
        with pytest.raises(SystemExit):
            cmd_workflow(_wf_args(path=".jobs.build.tags", remove_value="z"))

    def test_remove_by_index(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        release_yml = _init_workflow(tmp_path, monkeypatch)
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="a"))
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="b"))
        cmd_workflow(_wf_args(path=".jobs.build.tags", append_value="c"))
        # Remove index 1 ("b") — use _STDIN sentinel for remove_value since
        # it's positional removal
        from uv_release_monorepo.cli.workflow import _STDIN

        cmd_workflow(_wf_args(path=".jobs.build.tags", remove_value=_STDIN, at_index=1))
        doc = yaml.safe_load(release_yml.read_text())
        assert doc["jobs"]["build"]["tags"] == ["a", "c"]

    def test_remove_dict_key(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _init_workflow(tmp_path, monkeypatch)
        # Add id-token permission then remove it
        cmd_workflow(_wf_args(path=".permissions.id-token", set_value="write"))
        capsys.readouterr()
        cmd_workflow(_wf_args(path=".permissions", remove_value="id-token"))
        out = capsys.readouterr().out
        assert "Removed" in out


class TestCmdWorkflowOnKey:
    """Verify the YAML ``on:`` key survives round-tripping (PyYAML parses it as True)."""

    def test_set_preserves_on_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        release_yml = _init_workflow(tmp_path, monkeypatch)
        cmd_workflow(_wf_args(path=".permissions.id-token", set_value="write"))
        text = release_yml.read_text()
        # Must not contain `true:` — should be `on:` or `'on':`
        assert "\ntrue:" not in text
        doc = yaml.safe_load(text)
        # PyYAML reads `on:` / `'on':` back as True or "on" — either way,
        # the workflow_dispatch trigger must be present
        trigger = doc.get(True) or doc.get("on")
        assert trigger is not None
        assert "workflow_dispatch" in trigger
