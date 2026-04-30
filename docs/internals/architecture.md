# Architecture

`uvr` plans locally and executes remotely. All intelligence lives in `uvr release` on your machine. CI receives a single JSON plan and follows it mechanically.

## The two-phase pipeline

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
  1. validate  -  confirm plan
  2. build     -  per-runner, topo-ordered
  3. release   -  GitHub releases + wheels
  4. publish   -  PyPI (optional)
  5. bump      -  patch versions, tags, push
```

The local phase does all the thinking. It reads your workspace, figures out what changed, resolves the dependency graph, computes every version number, and produces a self-contained plan. The CI phase just follows instructions.

## Why this design

**Debug locally.** `uvr release --dry-run` shows the full plan without dispatching. You see exactly what CI will do before it runs.

**Stable CI.** The workflow YAML does not encode repo-specific logic. Add packages, change deps, modify matrices. The YAML stays the same.

**Inspectable plans.** `--json` dumps the complete snapshot of what CI will do. Pipe it to `jq`, diff it between runs, or store it as an artifact.

## The four pillars

### `uvr version`. Automatic dependency pinning

Computes published versions for every workspace package and rewrites internal dependency constraints automatically. See the [change detection](change-detection.md) and [pipeline](pipeline.md) pages for details.

### `uvr build`. Layered builds without sources

Builds packages in topological layers with `--find-links`. Unchanged dependencies are fetched from GitHub releases or CI run artifacts. Changed packages are built in order so earlier wheels satisfy later `[build-system].requires`. Per-runner matrix with sequential execution within layers. See the [build](build.md) page for details.

### Workflow. A CI template you never debug

The workflow YAML is a thin executor driven by `fromJSON(inputs.plan)`. Add your own jobs by editing the YAML. `uvr workflow validate` catches problems locally.

### `uvr release`. From git diff to published wheels

Change detection via baseline tags, transitive propagation, GitHub releases, PyPI publishing, and atomic version bumping. Skip and reuse flags let you recover from partial failures. See the [pipeline](pipeline.md) page for details.

## The workflow as a thin executor

The workflow YAML never changes when your repo structure changes. Add packages, change dependency graphs, modify build matrices. The YAML stays the same. All intelligence is in the plan JSON, and the workflow just reads it.

```yaml
# This drives the entire build matrix.
# Works for 1 package or 100, 1 runner or 10.
strategy:
  matrix:
    runner: ${{ fromJSON(inputs.plan).build_matrix }}
```

The five core jobs have mandatory `needs` dependencies that enforce pipeline order.

```
validate -> build -> release -> publish -> bump
```

`uvr jobs <job_name>` reads commands from the plan JSON and executes them. CI runs zero logic of its own.

## Plan JSON structure

The plan is serialized as JSON and passed via `gh workflow run release.yml -f plan=<json>`. CI accesses fields via <code v-pre>${{ fromJSON(inputs.plan).field }}</code>.

| Field | Purpose |
|---|---|
| `build_matrix` | Unique runner sets that drive the CI `strategy.matrix` |
| `python_version` | Python version for CI (default `"3.12"`) |
| `publish_environment` | GitHub Actions environment for trusted publishing |
| `skip` | Job names to skip |
| `reuse_run` | Workflow run ID to reuse artifacts from |
| `reuse_releases` | Whether to reuse existing GitHub releases |
| `jobs` | Ordered list of Job objects with commands |
| `changes` | Detected package changes |
