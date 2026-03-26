# Guide

This is the full reference for uv-release-monorepo. If you just want to get started, the [README](../packages/uv-release-monorepo/README.md) has a three-command quick start.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) installed
- A git repository hosted on GitHub with Actions enabled
- A workspace root `pyproject.toml` with `[tool.uv.workspace]` members defined
- The [GitHub CLI](https://cli.github.com/) (`gh`) authenticated — only needed if you want `uvr release` to dispatch workflows automatically

## Setting Up Your First Release

Install uvr as a uv tool:

```bash
uv tool install uv-release-monorepo
```

Then scaffold the release workflow:

```bash
uvr init
```

This generates `.github/workflows/release.yml` from a Pydantic model (`ReleaseWorkflow`). The workflow is a pure executor — it reads a `ReleasePlan` JSON and does exactly what it says. All seven jobs (four hook slots plus build, publish, finalize) are always present; unconfigured hooks default to a no-op step and are auto-skipped in the plan.

To regenerate the workflow (discarding any manual edits but preserving existing hooks):

```bash
uvr init
```

`uvr init` creates a fresh workflow from the model defaults. If `release.yml` already exists, it refuses without `--force`. Use `uvr validate` to check an existing file.

To regenerate and discard hooks too:

```bash
uvr init --force
```

To verify what was generated:

```bash
uvr status
```

### Configuring runners

By default every package builds on `ubuntu-latest`. If a package needs native compilation on multiple platforms, use the `uvr runners` command:

```bash
uvr runners my-native-pkg --add macos-14
uvr runners my-native-pkg --add windows-latest
uvr runners another-pkg --add macos-14
```

To remove a runner or clear all runners for a package:

```bash
uvr runners my-native-pkg --remove windows-latest
uvr runners my-native-pkg --clear
```

To see the current runner configuration:

```bash
uvr runners             # show all packages
uvr runners my-pkg      # show runners for one package
```

Runner configuration is stored in `[tool.uvr.matrix]` in your workspace root `pyproject.toml`.

### Filtering packages

If your workspace contains packages that shouldn't be part of the release cycle, add `[tool.uvr.config]` to your workspace root `pyproject.toml`:

```toml
[tool.uvr.config]
include = ["pkg-alpha", "pkg-beta"]   # allowlist: only these packages
exclude = ["pkg-internal"]            # denylist: skip these packages
```

If `include` is set, only listed packages are considered. `exclude` is applied after `include`. Both are optional — omit both to manage all workspace packages.

## Releasing

When you're ready to release:

```bash
uvr release
```

This does three things:

1. **Discovery** — Scans the workspace and diffs each package against its last dev baseline tag. Only packages with new commits (plus their downstream dependents) are included.
2. **Plan** — Builds a `ReleasePlan` JSON containing every package to build, its version, precomputed release notes, the runner matrix, and control fields like `skip` and `reuse_run_id`.
3. **Prompt** — Prints a human-readable summary (packages, dependency pins, and a pipeline view showing topo build layers per runner) and asks `Dispatch release? [y/N]`. If you confirm, the plan is dispatched to GitHub Actions via `gh workflow run`.

To skip the confirmation prompt (useful in scripts):

```bash
uvr release -y
```

### Forcing a full rebuild

```bash
uvr release --rebuild-all
```

Ignores change detection and rebuilds every package in the workspace.

### Pinning the Python version

```bash
uvr release --python 3.11
```

Sets the Python version used in CI builds. Defaults to `3.12`.

### Skipping jobs

You can skip individual jobs or jump to a specific point in the pipeline:

```bash
uvr release --skip pre-build               # skip a single job (repeatable)
uvr release --skip pre-build --skip post-build  # skip multiple jobs
uvr release --skip-to publish              # skip everything before publish
```

Valid job names: `pre-build`, `build`, `post-build`, `pre-release`, `publish`, `finalize`, `post-release`.

### Reusing artifacts from a previous run

If a build already succeeded but a later job failed, you can reuse the artifacts without rebuilding:

```bash
uvr release --skip-to publish --reuse-run 12345678
```

`--reuse-run RUN_ID` tells the publish job to download artifacts from a previous workflow run instead of the current one. It requires build to be skipped (via `--skip build` or `--skip-to`).

To skip both build and publish (e.g., to re-run only finalize):

```bash
uvr release --skip-to finalize --reuse-release
```

`--reuse-release` assumes GitHub releases already exist, so both build and publish must be skipped.

### Printing the raw plan JSON

```bash
uvr release --json
```

Prints the full `ReleasePlan` JSON alongside the human-readable summary. Useful for debugging or piping to other tools.

### Using the plan without dispatching

If you don't have `gh` installed or prefer to dispatch manually, just run `uvr release --json` and decline the prompt. The plan JSON is printed to stdout — you can copy it into the GitHub Actions "Run workflow" UI as the `plan` input.

## CI Workflow Architecture

The generated workflow always contains seven jobs that run in a fixed sequence:

```
pre-build → build → post-build → pre-release → publish → finalize → post-release
```

The four hook jobs (`pre-build`, `post-build`, `pre-release`, `post-release`) default to a no-op step and are auto-skipped in the release plan when they only contain the default no-op. The three core jobs are:

**build** — A matrix job with one entry per runner. Each runner builds all its assigned packages in topological dependency order using `uvr-steps build-all`. This ensures packages with build-time dependencies on siblings have those wheels available via `--find-links`. Wheels are uploaded as artifacts.

**publish** — A matrix job with one entry per changed package. Downloads the built wheels and creates a GitHub release using `softprops/action-gh-release@v2`. Release notes are precomputed in the plan, so this job needs no Python — just `download-artifact` + the release action. The `make_latest` field (driven by `[tool.uvr.config] latest`) controls which package gets the "Latest" badge.

**finalize** — Bumps patch versions, commits, creates dev baseline tags, and pushes to main.

### Frozen core jobs

The steps, strategy, and `if` conditions on `build`, `publish`, and `finalize` are frozen — `ReleaseWorkflow.model_validate()` rejects any modifications to these fields. This guarantees the core pipeline behaves identically across all projects. Hook jobs are the intended extension points.

## Mixed-Architecture Builds

When a package needs wheels for multiple platforms (e.g., a C extension), uvr expands the build matrix so each runner produces its own wheel.

```bash
uvr runners my-native-pkg --add ubuntu-latest
uvr runners my-native-pkg --add macos-14
```

On release, `my-native-pkg` will be built once on `ubuntu-latest` and once on `macos-14`. Both wheels are attached to the same GitHub release.

Packages without explicit runner assignments build only on `ubuntu-latest` (pure-Python wheels are platform-independent, so one runner is enough).

You can inspect and change runner assignments at any time:

```bash
uvr runners                               # see current config
uvr runners my-native-pkg --add macos-14  # add a runner
uvr runners my-native-pkg --remove macos-14  # remove a runner
```

## CI Hooks

Hooks let you inject custom steps into the release workflow at four points:

| Hook | When it runs |
|---|---|
| `pre-build` | Before the build matrix starts |
| `post-build` | After all build jobs finish |
| `pre-release` | Before the publish job |
| `post-release` | After the finalize job |

Each hook is its own GitHub Actions job with the correct `needs:` chain. All four are always present in `release.yml` — unconfigured hooks have a no-op default step and are automatically skipped in the release plan.

### Environment variables

Hook jobs can access the release plan via the workflow input:

- `${{ inputs.plan }}` — the full release plan JSON (available in `if:` conditions and step expressions)

You can also add an explicit step to export plan data to environment variables, for example:

```yaml
- name: Export plan context
  env:
    UVR_PLAN: ${{ inputs.plan }}
  run: |
    echo "UVR_CHANGED=$(echo "$UVR_PLAN" | jq -r '.changed | keys | join(" ")')" >> "$GITHUB_ENV"
    echo "UVR_PLAN=$UVR_PLAN" >> "$GITHUB_ENV"
```

### Editing hooks directly in release.yml

There is no separate hooks CLI — you edit `.github/workflows/release.yml` directly. Each hook job has a `steps:` array you can customize. After editing, run `uvr validate` to check your changes:

```bash
uvr validate
```

This loads the YAML, validates it through the `ReleaseWorkflow` model, and writes it back. If your edits broke the schema (e.g., you accidentally modified a frozen field on a core job), validation will fail with an error.

### Example: gate releases on tests

Edit the `pre-build` job in `release.yml`:

```yaml
  pre-build:
    runs-on: ubuntu-latest
    if: ${{ !contains(fromJSON(inputs.plan).skip, 'pre-build') }}
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - uses: astral-sh/setup-uv@v5
      with:
        python-version: ${{ fromJSON(inputs.plan).python_version }}
    - name: Lint, typecheck, and test
      run: |
        uv sync --all-packages
        uv run poe check
        uv run poe test
```

### Example: notify after release

Edit the `post-release` job in `release.yml`:

```yaml
  post-release:
    runs-on: ubuntu-latest
    if: ${{ always() && !failure() && !contains(fromJSON(inputs.plan).skip, 'post-release') }}
    needs:
    - finalize
    steps:
    - name: Slack notification
      env:
        UVR_PLAN: ${{ inputs.plan }}
      run: |
        CHANGED=$(echo "$UVR_PLAN" | jq -r '.changed | keys | join(", ")')
        curl -X POST "$SLACK_WEBHOOK" -d "{\"text\": \"Released: $CHANGED\"}"
```

## Installing from GitHub Releases

uvr can install workspace packages directly from their GitHub releases, resolving internal dependencies automatically.

### Local workspace packages

From within the repository that published the releases:

```bash
uvr install my-package           # latest version
uvr install my-package@1.2.3     # pinned version
```

This walks the workspace dependency graph, downloads the appropriate wheel for each internal dependency, and installs them all with `uv pip install`. External (PyPI) dependencies are resolved by pip from wheel metadata.

### Remote packages

To install a package published from a different repository:

```bash
uvr install acme/other-monorepo/my-package
uvr install acme/other-monorepo/my-package@1.2.3
```

Remote installs download and install the specified package directly. Your `gh` CLI must be authenticated with access to the target repository.

## How It Works

### The release flow

```
your machine                          GitHub Actions
─────────────                         ──────────────
uvr release
  ├─ scan workspace
  ├─ diff each package vs dev tag
  ├─ walk dependency graph
  ├─ precompute release notes
  ├─ expand build matrix
  ├─ print human-readable summary
  │   (packages, dep pins, pipeline)
  └─ [confirm] dispatch plan ────────► release.yml receives plan
                                         ├─ [hook] pre-build
                                         ├─ build: per-runner, topo-ordered
                                         ├─ [hook] post-build
                                         ├─ [hook] pre-release
                                         ├─ publish: one GitHub release
                                         │   per changed package
                                         │   (softprops/action-gh-release)
                                         ├─ finalize:
                                         │   ├─ bump patch versions
                                         │   ├─ commit & tag dev baselines
                                         │   └─ push
                                         └─ [hook] post-release
```

The workflow is a **pure executor**. It receives the plan as a single JSON input and follows it exactly. All intelligence — change detection, dependency resolution, matrix expansion, release notes — lives in the CLI on your machine. The plan JSON encodes everything: `uvr_version`, `python_version`, `skip` (list of jobs to skip), `reuse_run_id`, and the full build/publish matrices.

### Version bumping

You control **major.minor** by editing `version` in each package's `pyproject.toml`. CI controls **patch** — after every release, it bumps the patch number and appends `.dev0`, commits, and tags the dev baseline. Between releases, your pyproject.toml always shows the development version (e.g., `0.5.2.dev0`). On release, the `.dev0` is stripped automatically.

### Dependency pinning

When a package depends on another workspace package, uvr pins the internal dependency constraint to the just-published version before releasing. This ensures that published wheels remain installable even when only a subset of packages change in the next cycle. Pin updates are applied locally during `uvr release` — if any pins change, uvr tells you to commit them before proceeding.

## Tag Structure

uvr uses two kinds of git tags:

**Release tags** like `my-pkg/v1.2.3` are created for each changed package at release time. They double as the identifier for the corresponding GitHub release (where wheels are stored).

**Dev baseline tags** like `my-pkg/v1.2.4-dev` are placed on the version-bump commit immediately after a release. They serve as the diff base for the next release — only commits after this tag are considered new work.

```
commit A   ← my-pkg/v1.0.0      (released; wheels in the my-pkg/v1.0.0 GitHub release)
commit B   ← my-pkg/v1.0.1-dev  (pyproject.toml bumped to 1.0.1.dev0; new diff base)
commit C   … normal development …
commit D   ← my-pkg/v1.0.1      (released; wheels in the my-pkg/v1.0.1 GitHub release)
commit E   ← my-pkg/v1.0.2-dev  (pyproject.toml bumped to 1.0.2.dev0; new diff base)
```

## Publishing to PyPI

The release workflow creates GitHub releases with wheels attached. To also publish to PyPI, edit the `post-release` job in `.github/workflows/release.yml` to download the wheel and publish it using [trusted publishing](https://docs.pypi.org/trusted-publishers/).

Here is a complete example for a package called `my-package`:

```yaml
  post-release:
    runs-on: ubuntu-latest
    if: ${{ always() && !failure() && !contains(fromJSON(inputs.plan).skip, 'post-release') }}
    needs:
    - finalize
    environment: pypi
    steps:
    - name: Download wheel for PyPI
      if: fromJSON(inputs.plan).changed['my-package'] != null
      env:
        GH_TOKEN: ${{ github.token }}
        UVR_PLAN: ${{ inputs.plan }}
      run: |
        VERSION=$(echo "$UVR_PLAN" | python3 -c "import sys,json; print(json.load(sys.stdin)['changed']['my-package']['version'])")
        mkdir -p dist
        gh release download "my-package/v${VERSION}" --repo "${{ github.repository }}" --pattern "my_package-*.whl" --dir dist
    - name: Publish to PyPI
      if: fromJSON(inputs.plan).changed['my-package'] != null
      uses: pypa/gh-action-pypi-publish@release/v1
```

You also need `id-token: write` in the workflow's top-level `permissions` for trusted publishing. Add it to `release.yml` next to `contents: write`:

```yaml
permissions:
  contents: write
  id-token: write
```

The `environment: pypi` on the job ties it to a [GitHub deployment environment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment) configured with your PyPI trusted publisher. The `if:` condition on each step ensures they only run when the target package was actually released.

After editing, run `uvr validate` to check:

```bash
uvr validate
```

## Command Reference

### `uvr init`

Scaffold the GitHub Actions release workflow.

```
uvr init [--force] [--workflow-dir DIR]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--force` | — | Overwrite existing `release.yml` with fresh defaults |
| `--workflow-dir` | `.github/workflows` | Directory to write the workflow file |

Fails if `release.yml` already exists (use `--force` to overwrite). After generating, edit the file to add your hook steps, then run `uvr validate` to check.

### `uvr validate`

Validate an existing `release.yml` against the `ReleaseWorkflow` model.

```
uvr validate [--workflow-dir DIR]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--workflow-dir` | `.github/workflows` | Directory containing the workflow file |

Reports errors for invalid structure (missing required jobs, wrong types) and warnings for modified core job fields (build, publish, finalize steps/strategy).

### `uvr runners`

Manage per-package build runners.

```
uvr runners [PKG] [--add RUNNER | --remove RUNNER | --clear]
```

| Argument/Flag | Description |
|---------------|-------------|
| `PKG` | Package name (omit to show all) |
| `--add RUNNER` | Add a runner for the package |
| `--remove RUNNER` | Remove a runner from the package |
| `--clear` | Remove all runners for the package |

Runner configuration is stored in `[tool.uvr.matrix]` in your workspace root `pyproject.toml`.

### `uvr release`

Generate a release plan and optionally dispatch it to GitHub Actions.

```
uvr release [-y] [--rebuild-all] [--python VERSION] [--skip JOB] [--skip-to JOB]
            [--reuse-run RUN_ID] [--reuse-release] [--json] [--workflow-dir DIR]
```

| Flag | Default | Description |
|------|---------|-------------|
| `-y`, `--yes` | — | Skip confirmation prompt and dispatch immediately |
| `--rebuild-all` | — | Rebuild all packages regardless of changes |
| `--python` | `3.12` | Python version for CI builds |
| `--skip` | — | Skip a job (repeatable). Valid: `pre-build`, `build`, `post-build`, `pre-release`, `publish`, `finalize`, `post-release` |
| `--skip-to` | — | Skip all jobs before the named job |
| `--reuse-run` | — | Download build artifacts from a previous workflow run (requires build to be skipped) |
| `--reuse-release` | — | Assume GitHub releases already exist (requires build and publish to be skipped) |
| `--json` | — | Also print the raw plan JSON |
| `--workflow-dir` | `.github/workflows` | Directory containing the workflow file |

### `uvr run`

Execute the release pipeline locally (for testing or CI).

```
uvr run [--dry-run] [--rebuild-all] [--no-push] [--plan JSON]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--dry-run` | — | Print what would be released without making changes |
| `--rebuild-all` | — | Rebuild all packages |
| `--no-push` | — | Skip git push |
| `--plan` | — | Execute a pre-computed release plan JSON |

### `uvr status`

Show the current workflow configuration, build matrix, and which packages have changed.

```
uvr status [--workflow-dir DIR]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--workflow-dir` | `.github/workflows` | Directory containing the workflow file |

### `uvr install`

Install a workspace package and its internal dependencies from GitHub releases.

```
uvr install PACKAGE[@VERSION]
uvr install ORG/REPO/PACKAGE[@VERSION]
```

## Configuration Reference

All uvr configuration lives in the workspace root `pyproject.toml`:

```toml
[tool.uvr.matrix]
my-native-pkg = ["ubuntu-latest", "macos-14"]
my-python-pkg = ["ubuntu-latest"]

[tool.uvr.config]
include = ["pkg-alpha", "pkg-beta"]   # optional allowlist
exclude = ["pkg-internal"]            # optional denylist
```
