# Architecture

<code class="brand-code">uvr</code> plans locally and executes remotely. All intelligence lives in <code class="brand-code">uvr release</code> on your machine. CI receives a single JSON plan and follows it mechanically.

```
uvr release (your machine)
  1. scan workspace (pyproject.toml)
  2. diff each package vs baseline tag
  3. propagate changes through deps
  4. compute release and next versions
  5. pin internal dependencies
  6. expand per-runner build matrix
  7. generate all commands
  8. print human-readable summary
  9. dispatch plan JSON to GitHub Actions

release.yml (GitHub Actions)
  1. validate: confirm plan
  2. build: per-runner, topo-ordered
  3. release: GitHub releases + wheels
  4. publish: PyPI (optional)
  5. bump: patch versions, tags, push
```

- **Debug locally.** <code class="brand-code">uvr release --dry-run</code> shows the full plan without dispatching.
- **Stable CI.** The workflow YAML doesn't encode repo-specific logic. Add packages, change deps, modify matrices. The YAML stays the same.
- **Inspectable plans.** `--json` dumps the complete snapshot of what CI will do.

## The four pillars

### [<code class="brand-code">uvr bump</code>](02-bump.md): Automatic dependency pinning

Computes published versions for every workspace package and rewrites internal dependency constraints automatically.

### [<code class="brand-code">uvr build</code>](03-build.md): Layered builds without sources

Builds packages in topological layers with `--find-links`. Unchanged dependencies are fetched from GitHub releases (or CI run artifacts). Changed packages are built in order so earlier wheels satisfy later `[build-system].requires`. Per-runner matrix with sequential execution within layers.

### [<code class="brand-code">uvr workflow</code>](04-workflow.md): A CI template you never debug

Workflow YAML is a thin executor driven by `fromJSON(inputs.plan)`. Frozen fields protect critical expressions. Add your own jobs by editing the YAML. <code class="brand-code">uvr workflow validate</code> catches problems locally.

### [<code class="brand-code">uvr release</code>](05-release.md): From `git diff` to published wheels

Change detection via baseline tags, transitive propagation, GitHub releases, PyPI publishing, and atomic version bumping. Skip and reuse flags let you recover from partial failures.
