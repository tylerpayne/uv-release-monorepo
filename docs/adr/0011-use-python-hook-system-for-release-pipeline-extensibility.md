# Use Python Hook System For Release Pipeline Extensibility

* Status: accepted
* Date: 2026-03-27

## Context and Problem Statement

Users need to inject custom data (e.g., locally computed variables) into the release plan so that CI stays executor-focused — it runs the plan, not computes it. How should uvr let users extend the planning and execution pipeline without forking the tool or editing generated workflow YAML?

## Decision Drivers

* The release plan must remain the single source of truth for CI — custom data belongs in the plan, not in CI logic
* The extension mechanism should be familiar to Python developers
* Hook discovery should work with zero config for simple cases

## Considered Options

* Python hook class system (inspired by hatch_build)
* Config-only approach (TOML keys mapped to shell commands)
* No extension system — users edit the workflow YAML directly

| Criterion | Python hooks | Config-only | Edit YAML |
|---|---|---|---|
| Can inject computed data into plan | Yes — full Python at plan time | No — shell commands can't modify the plan object | No — YAML edits happen after dispatch |
| Familiarity | Follows hatch_build pattern | Novel convention | Already known |
| Zero-config discovery | Yes — convention file `uvr_hooks.py` | Yes — TOML only | N/A |
| CI stays executor-only | Yes — hooks run locally during planning | Partially — shell commands could run in CI too | No — pushes logic into CI |
| Maintenance burden | New public API to support | Minimal | None |

## Decision Outcome

Chosen option: "Python hook class system", because it is the only option that lets users inject locally computed and tested values into the plan while keeping CI as a pure executor. The hatch_build pattern is well-known in the Python packaging ecosystem.

### Positive Consequences

* Users can extend planning (pre_plan/post_plan) and execution (pre/post build/publish/finalize) without touching workflow YAML
* Extra keys injected by hooks survive JSON round-trips via Pydantic's `model_extra`, so CI sees them without schema changes
* Convention-based discovery (`uvr_hooks.py` with class `Hook`) means zero config for the common case

### Negative Consequences

* `ReleaseHook` is now a public API — breaking changes require a major version bump
* Hook classes are imported and executed locally, so a broken hook can block `uvr release`
* The hook point names (pre_plan, post_plan, pre_build, etc.) are frozen once users depend on them

## Links

* Supersedes [ADR-0006: Use post-release hook for PyPI publishing](0006-use-post-release-hook-for-pypi-publishing.md) — PyPI publishing can now be implemented as a ReleaseHook instead of a workflow-level hook job
