# Architecture

<code class="brand-code">uvr</code> plans locally and executes remotely. All intelligence lives in <code class="brand-code">uvr release</code> on your machine. CI receives a single JSON plan and follows it mechanically.

```
your machine                           GitHub Actions
─────────────                          ──────────────
uvr release
  ├─ scan workspace
  ├─ diff each package vs baseline tag
  ├─ propagate changes through deps
  ├─ compute release & next versions
  ├─ pin internal dependencies
  ├─ expand per-runner build matrix
  ├─ generate all commands
  ├─ print human-readable summary
  └─ [confirm] dispatch plan ─────────► release.yml receives plan JSON
                                          ├─ validate plan schema
                                          ├─ build: per-runner, topo-ordered
                                          ├─ release: GitHub releases + wheels
                                          ├─ publish: PyPI (optional)
                                          └─ bump: patch versions, tags, push
```

- **Debug locally.** <code class="brand-code">uvr release --dry-run</code> shows the full plan without dispatching.
- **Stable CI.** The workflow YAML doesn't encode repo-specific logic. Add packages, change deps, modify matrices. The YAML stays the same.
- **Inspectable plans.** `--json` dumps the complete snapshot of what CI will do.

## The four pillars

### [<code class="brand-code">uvr bump</code>](02-bump.md): Automatic dependency pinning

Computes published versions for every workspace package and rewrites internal dependency constraints automatically.

### [<code class="brand-code">uvr build</code>](03-build.md): Layered builds without sources

Builds packages in topological layers with `--find-links`. Unchanged dependencies are fetched from GitHub releases (or CI run artifacts). Changed packages are built in order so earlier wheels satisfy later `[build-system].requires`. Per-runner matrix with concurrent execution within layers.

### [<code class="brand-code">uvr workflow</code>](04-workflow.md): A CI template you never debug

Workflow YAML is a thin executor driven by `fromJSON(inputs.plan)`. Frozen fields protect critical expressions. Add your own jobs by editing the YAML. <code class="brand-code">uvr workflow validate</code> catches problems locally.

### [<code class="brand-code">uvr release</code>](05-release.md): From `git diff` to published wheels

Change detection via baseline tags, transitive propagation, GitHub releases, PyPI publishing, and atomic version bumping. Skip and reuse flags let you recover from partial failures.
