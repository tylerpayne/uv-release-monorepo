# Releasing Packages

## The standard release

```bash
uvr release
```

`uvr release` detects what changed, pins dependencies, and plans a topologically ordered build, publish, and bump. Everything is validated locally before dispatch. Version conflicts, stale pins, and dirty working trees are caught on your machine, not in CI. See [Architecture](../internals/architecture.md) for the full pipeline.

A clean working tree is required. `uvr release` errors if you have uncommitted changes or if your local branch is out of sync with the remote.

## Preview before dispatching

Run a dry run to see the plan without changing anything.

```bash
uvr release --dry-run
```

Export the plan as JSON for inspection or for re-dispatching later through the GitHub Actions UI.

```bash
uvr release --json
```

## Choose what to release

By default, `uvr release` releases every package whose files changed since its last release (and any dependents). Override the selection when you need to.

```bash
uvr release --packages pkg-alpha pkg-beta    # force specific packages (and their dependents)
uvr release --not-packages pkg-debug         # exclude specific packages
uvr release --all-packages                   # treat every package as changed
```

To bump major or minor instead of patch, run `uvr version` before `uvr release`. See [Managing Versions](versions.md) for the full version lifecycle.

```bash
uvr version --bump minor
uvr release
```

## Customize the release

```bash
uvr release --release-notes pkg-alpha "Fixed the widget serializer"
uvr release --release-notes pkg-alpha @notes/alpha.md
```

`--release-notes` is repeatable for multiple packages. Use `@path` to read from a file.

```bash
uvr release --runners ubuntu-latest macos-latest
```

`--runners` filters the build matrix to specific runner labels.

```bash
uvr release --dev
```

`--dev` publishes the `.devN` version as is instead of stripping it. Useful for testing packages from an index before committing to a real release.

```bash
uvr release -y
```

`-y` skips the interactive confirmation prompt.

The Python version for CI builds is set in `[tool.uvr.config]`. See [Configuration](configuration.md) for all configuration keys.

## Run the pipeline locally

```bash
uvr release --where local
```

Runs the full pipeline on your machine instead of dispatching to CI. Add `--no-push` to skip git push and `--no-commit` to skip git commit.

## Recover from a failure

The release pipeline runs five jobs in order. `validate`, `build`, `release`, `publish`, then `bump`. If any job fails, resume from where it broke. You do not need to start over.

### Build failed

Nothing was published. Fix the issue and re-run.

```bash
uvr release
```

### Build succeeded, release failed

Reuse the build artifacts from the prior run.

```bash
uvr release --skip-to release --reuse-run <RUN_ID>
```

Get the run ID from the GitHub Actions URL or `gh run list`.

### Release succeeded, publish or bump failed

Pass `--packages` to name the packages you just released. Bump does not need wheel artifacts, so no `--reuse-*` flag is required.

```bash
uvr release --skip-to bump --packages pkg-alpha pkg-beta
```

If publish failed and you want to retry it before bump, reuse the existing GitHub releases.

```bash
uvr release --skip-to publish --reuse-releases --packages pkg-alpha pkg-beta
```

### Custom job failed

Skip the core jobs and re-dispatch.

```bash
uvr release --skip build --skip release --skip bump
```

Or re-dispatch through the GitHub Actions UI with the original plan JSON.

### Skip and reuse flag reference

| Flag | Description |
|------|-------------|
| `--skip JOB` | Skip a single job (repeatable) |
| `--skip-to JOB` | Skip every job before JOB (except `validate`) |
| `--reuse-run RUN_ID` | Download artifacts from a prior CI run instead of building |
| `--reuse-releases` | Download wheels from existing GitHub releases instead of CI artifacts |

`--reuse-run` and `--reuse-releases` are mutually exclusive. Either one is only required when `release` or `publish` will run. `--skip-to bump` does not need any `--reuse-*` flag.

## Other commands

Build and install locally for testing.

```bash
uvr build                          # build changed packages to dist/
uvr build --packages pkg-alpha     # build specific packages and their deps
uvr build --all-packages           # build everything
uvr install --dist dist/           # install from a local build
```

Install or download released wheels from GitHub.

```bash
uvr install pkg-alpha              # latest release
uvr install pkg-alpha==1.2.0       # specific version
uvr install --run-id 12345678      # from CI artifacts
uvr download pkg-alpha             # download wheels without installing
uvr download pkg-alpha --all-platforms
```

Upgrade uvr and its bundled templates.

```bash
uv add --dev uv-release
uvr workflow install --upgrade     # merge template changes
uvr skill install --upgrade        # merge skill changes
```

Remove build caches.

```bash
uvr clean
```
