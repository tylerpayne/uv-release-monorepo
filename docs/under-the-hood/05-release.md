# <code class="brand-code">uvr release</code>: From `git diff` to Published Wheels

One command detects changes, builds on the right runners, creates GitHub releases, publishes to PyPI, bumps versions, and pushes. All planned locally, executed on CI. See [Change Detection](01-change-detection.md) for how packages are discovered and diffed.

## The ReleasePlan

The plan encodes everything CI needs.

| Field | Purpose |
|-------|---------|
| `changed` | Packages to rebuild, with version lifecycle and runner config |
| `unchanged` | Packages reused from previous releases |
| `build_commands` | Pre-computed build commands, keyed by runner |
| `release_commands` | GitHub release creation commands |
| `publish_commands` | PyPI publishing commands (if configured) |
| `bump_commands` | Version bump, dep pin, tag, and push commands |
| `build_matrix` | Unique runner sets (drives CI `strategy.matrix`) |
| `skip` | Job names to skip |
| `reuse_run_id` | Workflow run ID to reuse artifacts from |

The plan is serialized as JSON and passed via `gh workflow run release.yml -f plan=<json>`. CI accesses fields via <code v-pre>${{ fromJSON(inputs.plan).field }}</code>.

## The CI pipeline

### Validate

Confirms the plan schema version matches the deployed <code class="brand-code">uvr</code>.

### Build

One CI job per unique runner. Each job runs [topologically layered builds](03-build.md) and uploads wheels as `wheels-<runner-labels>`.

### Release

Downloads all `wheels-*` artifacts and creates one GitHub release per changed package.

```bash
uvr jobs release --plan "$UVR_PLAN"
```

Each release gets a tag (`{name}/v{version}`), release notes, and attached wheels. The `[tool.uvr.config].latest` setting controls the "Latest" badge.

### Publish (optional)

```toml
[tool.uvr.publish]
index = "pypi"                # index name (or URL)
environment = "pypi-publish"  # GitHub Actions environment for trusted publishing
exclude = ["pkg-debug"]       # packages to skip
```

Runs `uv publish` per changed package. The `environment` field enables [trusted publishing](https://docs.pypi.org/trusted-publishers/). No API tokens needed, just an OIDC trust relationship between your GitHub repo and PyPI.

### Bump

1. Bump to next [dev version](https://peps.python.org/pep-0440/#developmental-releases). `uv version {next}.dev0`
2. Pin internal deps to just-published versions (see [Bump](02-bump.md))
3. Sync lockfile, commit, tag baselines, push

This is the only CI job that writes to the repository.

## Local execution

<code class="brand-code">uvr release --where local</code> runs the full pipeline on your machine. Useful for pure-Python packages that only need one runner.

## Skip and reuse

### `--skip <job>`

Skip a specific job. Downstream jobs still run.

### `--skip-to <job>`

Skip all jobs before the named job.

```bash
uvr release --skip-to uvr-release
```

### `--reuse-run <run-id>`

Reuse artifacts from a previous build.

```bash
uvr release --skip uvr-build --reuse-run 12345
```
