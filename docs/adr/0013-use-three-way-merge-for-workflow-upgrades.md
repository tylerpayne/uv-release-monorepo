# Use Three Way Merge For Workflow Upgrades

* Status: accepted
* Date: 2026-03-27

## Context and Problem Statement

When uvr upgrades the release workflow (`release.yml`), it must update the core pipeline jobs while preserving user customizations (custom jobs, modified permissions, etc.). The previous approach — static template apply followed by `git checkout -p` — was brittle and frequently lost or mangled user edits. How should `uvr upgrade` merge template changes with user customizations?

## Decision Drivers

* User customizations to the workflow must survive upgrades
* The merge must be deterministic and automatable (no interactive prompts in CI)
* Conflicts between template changes and user edits must be surfaced clearly, not silently dropped

## Considered Options

* Three-way merge (old template as base, new template as theirs, current file as ours)
* Diff-and-patch (generate a patch from old->new template, apply to current file)
* Separate managed/user sections (marker comments delineating regions)

| Criterion | Three-way merge | Diff-and-patch | Marker sections |
|---|---|---|---|
| Preserves user edits | Yes — standard merge semantics | Usually — but hunks fail if context shifted | Yes — but only outside markers |
| Handles template + user both changed same region | Conflict markers — user decides | Patch rejection — user manually applies | Not possible — regions are exclusive |
| Complexity | Moderate — needs base version tracking | Low — just `diff` + `patch` | Low — string splitting |
| User freedom | Full — edit anywhere in the file | Full — but risky if edits overlap template regions | Restricted — must stay in user sections |
| Failure mode | Explicit conflict markers | Silent patch failure or fuzz-applied hunk in wrong place | Silent loss if user edits inside managed section |

## Decision Outcome

Chosen option: "Three-way merge", because it uses well-understood merge semantics to combine template updates with user customizations, and surfaces conflicts explicitly rather than silently dropping changes. The previous static-apply approach was a degenerate case of diff-and-patch that proved brittle in practice.

The base version for the three-way merge is tracked via commit recording — uvr remembers which template version was last applied, enabling clean diffs.

### Positive Consequences

* Users can edit any part of the workflow file — no restricted zones
* Template updates that don't conflict with user edits apply cleanly and automatically
* Conflicts produce standard merge markers that developers already know how to resolve

### Negative Consequences

* Requires tracking the base template version (the "old" side of the merge), adding state to manage
* Three-way merge can still produce conflicts that require manual resolution
* More complex implementation than simple file overwrite — merge logic must handle YAML correctly at the text level
