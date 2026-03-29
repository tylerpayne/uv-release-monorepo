"""Tests for bundled release workflow template."""

from __future__ import annotations

from uv_release_monorepo.cli.init import _latest_template_version, _load_template_yaml
from uv_release_monorepo.shared.models.workflow import ReleaseWorkflow


def _template_workflow() -> dict:
    version = _latest_template_version()
    return _load_template_yaml(version)


def test_template_has_name() -> None:
    doc = _template_workflow()
    assert doc["name"] == "Release Wheels"


def test_template_has_plan_input() -> None:
    doc = _template_workflow()
    inputs = doc["on"]["workflow_dispatch"]["inputs"]
    assert "plan" in inputs
    assert inputs["plan"]["required"] is True


def test_template_has_core_jobs() -> None:
    doc = _template_workflow()
    jobs = doc["jobs"]
    assert "build" in jobs
    assert "release" in jobs
    assert "finalize" in jobs


def test_template_validates_against_model() -> None:
    """The bundled template passes pydantic structural validation."""
    doc = _template_workflow()
    ReleaseWorkflow.model_validate(doc)


def test_template_job_needs_chain() -> None:
    doc = _template_workflow()
    jobs = doc["jobs"]
    assert "validate_plan" in jobs["build"]["needs"]
    assert "build" in jobs["release"]["needs"]
    assert "release" in jobs["finalize"]["needs"]


def test_template_default_permissions() -> None:
    doc = _template_workflow()
    assert doc["permissions"] == {"contents": "write"}


def test_template_core_jobs_have_executor_steps() -> None:
    doc = _template_workflow()
    build_steps = doc["jobs"]["build"]["steps"]
    assert any("uvr build" in str(s.get("run", "")) for s in build_steps)

    release_steps = doc["jobs"]["release"]["steps"]
    assert any(
        s.get("uses", "").startswith("softprops/action-gh-release")
        for s in release_steps
    )

    finalize_steps = doc["jobs"]["finalize"]["steps"]
    assert any("uvr finalize" in str(s.get("run", "")) for s in finalize_steps)
