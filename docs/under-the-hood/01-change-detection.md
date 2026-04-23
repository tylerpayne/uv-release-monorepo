# Change Detection

<code class="brand-code">uvr</code> determines which packages need releasing by diffing each package against its baseline tag and propagating dirtiness through the dependency graph.

## Tag formats

<code class="brand-code">uvr</code> uses two kinds of git tags.

### Release tags: `{name}/v{version}`

Created during the release phase. These mark the commit where a version was published and double as identifiers for GitHub releases (where wheels are stored).

```
pkg-alpha/v0.1.5
pkg-beta/v0.2.0
pkg-gamma/v1.0.0a0
```

### Baseline tags: `{name}/v{version}-base`

Created during the bump phase, on the commit that bumps to the next [dev version](https://peps.python.org/pep-0440/#developmental-releases). These are the diff base for the next release. Only commits *after* this tag are considered new work.

```
pkg-alpha/v0.1.6.dev0-base
pkg-beta/v0.2.1.dev0-base
pkg-gamma/v1.0.0a1.dev0-base
```

### The lifecycle

```
commit A  ← pkg-alpha/v0.1.5              (release tag)
commit B  ← pkg-alpha/v0.1.6.dev0-base    (baseline; pyproject.toml bumped to 0.1.6.dev0)
commits   … development …
commit C  ← pkg-alpha/v0.1.6              (release tag)
commit D  ← pkg-alpha/v0.1.7.dev0-base    (baseline; pyproject.toml bumped to 0.1.7.dev0)
```

The baseline tag sits on the bump commit, not the release commit. This means the version bump itself is excluded from the next release's diff.

## Package discovery

`Workspace.parse()` reads `[tool.uv.workspace].members`, expands globs, collects metadata (name, version, internal deps), and applies `[tool.uvr.config]` filters.

```toml
[tool.uvr.config]
include = ["pkg-alpha", "pkg-beta"]   # allowlist
exclude = ["pkg-debug"]               # denylist
```

## Diffing

A package is **dirty** if any of these conditions hold.

1. `--all-packages` is set
2. No baseline tag exists (first release)
3. Files in the package directory changed since baseline (subtree comparison via pygit2)
4. The version is clean (no `.dev` suffix). The previous release tag is found and used as the diff baseline.

## Transitive propagation

After direct dirtiness is determined, changes propagate **upward** through the dependency graph via BFS over a reverse dependency map.

```
pkg-alpha changes
  → pkg-beta marked dirty   (depends on alpha)
  → pkg-delta marked dirty  (depends on alpha)
  → pkg-gamma marked dirty  (depends on beta, transitively)
```

[Post-release](https://peps.python.org/pep-0440/#post-releases) packages don't propagate. A post-fix only affects the target package, not its dependents.
