# Unify Version Management Under Single Command

* Status: accepted
* Date: 2026-04-30

## Context and Problem Statement

The current `uvr bump` command handles too many distinct operations through a single flag group: `--dev`, `--patch`, `--minor`, `--major`, `--alpha`, `--beta`, `--rc`, `--stable`, `--post`, and `--promote`. The `--stable` flag is confusing because it strips both the dev suffix and pre-release suffix (`0.31.0a8.dev0` becomes `0.31.0`), when users often expect it to only strip dev (`0.31.0a8`). There is no command to read or directly set versions. Additionally, dependency pins currently reference dev versions, which breaks `pip install` on PyPI since dev versions are not resolvable without `--pre`. Unlike `uv version --bump`, which only modifies a single package's version field, `uvr` must also update internal dependency pins across the workspace. How should version management be structured so that each operation has clear semantics and pins always reference installable versions?

## Decision Drivers

* Each version operation (read, set, increment, promote) should have distinct, predictable semantics that don't overlap
* Dependency pins must always reference non-dev versions so that released wheels are installable from PyPI without `--pre`
* The command must be workspace-aware: auto-detecting changed packages, supporting `--packages`, `--all-packages`, and `--not-packages` for scoping
* The distinction from `uv version` must be clear. `uvr version` manages versions AND their downstream dependency pins across the workspace, not just a single version field

## Considered Options

* Single `uvr version` command with `--set`, `--bump`, `--promote` modes
* Three separate commands: `uvr version`, `uvr bump`, `uvr promote`
* Keep current `uvr bump` and add missing features

## Decision Outcome

Chosen option: "Single `uvr version` command with `--set`, `--bump`, `--promote` modes", because it groups all version operations under one discoverable entry point with clear modal semantics, and it avoids the overloaded flag list that caused the `--stable` confusion. The breaking change (removing `uvr bump`) is acceptable because uvr is pre-1.0 and the current `uvr bump` interface has proven confusing in practice.

### Positive Consequences

* One command to learn for all version operations
* Pin logic lives in one place with a single rule: never pin to dev versions
* `--promote` without arguments auto-advances the release stage, eliminating the `--stable` confusion
* `--not-packages` exclusion supported uniformly across all modes

### Negative Consequences

* Breaking change for existing `uvr bump` users. Migration is mechanical (`uvr bump --patch` becomes `uvr version --bump patch`) but scripts and muscle memory need updating.
* `uvr version --bump patch` is more characters than `uvr bump --patch` for the most common operation
* Name collision with `uv version` may confuse users who expect identical behavior. The distinction (single-package vs workspace-wide with pin management) must be documented clearly.

## Comparison

| Criterion | Single `uvr version` | Three commands | Extend `uvr bump` |
|---|---|---|---|
| Discoverability | One place for all version ops | Must know which verb to use | Overloaded flag list grows further |
| Semantic clarity | Flags name the operation mode | Verb names the operation | `bump --set` is contradictory |
| Pin management | Centralized, same for all modes | Duplicated across commands or shared via library | Already exists but dev pin bug remains |
| Package scoping | One set of `--packages`/`--all-packages`/`--not-packages` | Repeated on each command | Repeated on each command |
| Typing for common case | `uvr version --bump patch` (more chars) | `uvr bump patch` (fewer chars) | `uvr bump --patch` (current) |
| Backward compat | Breaking, removes `uvr bump` | Additive, keeps `uvr bump` | Non-breaking |
| Distinction from `uv version` | Same noun, different tool. Clear from the `uvr` prefix and pin behavior | Different verbs avoid confusion | `bump` doesn't collide |
