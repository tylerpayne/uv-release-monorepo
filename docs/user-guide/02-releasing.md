# Releasing Packages

## The standard release

```bash
uvr release
```

<code class="brand-code">uvr release</code> detects changes, pins dependencies, and plans a topologically ordered build, publish, and bump. Validates everything locally before dispatch. Version conflicts, stale pins, and dirty working trees are caught on your machine, not in CI. See [Architecture](../under-the-hood/architecture.md) for the full pipeline.

## Preview without releasing

```bash
uvr release --dry-run
```

Runs all detection and planning logic but makes no changes.

## Export plan as JSON

```bash
uvr release --json
```

## Bump versions before releasing

To release a minor or major version instead of patch, bump first and then release.

```bash
uvr bump --minor
uvr release
```

Available bump types. `alpha`, `beta`, `rc`, `post`, `dev`, `stable`, `minor`, `major`, `patch`. See [Managing Versions](04-versions.md) for the full version lifecycle.

## Publish dev versions

```bash
uvr release --dev
```

Publishes the `.devN` version as-is instead of stripping it.

## Set release notes

```bash
uvr release --release-notes pkg-alpha "Fixed the widget serializer"
uvr release --release-notes pkg-alpha @notes/alpha.md
```

The flag is repeatable for multiple packages.

## Skip confirmation

```bash
uvr release -y
```

## Build and release locally

```bash
uvr release --where local
```

Runs the full pipeline (build, release, publish, bump) on your machine instead of dispatching to CI. Add `--no-push` to skip git push.

## Clean working tree

A clean working tree is required. <code class="brand-code">uvr release</code> will error if you have uncommitted changes or if your local branch is out of sync with the remote.

## Release specific packages

```bash
uvr release --packages pkg-alpha pkg-beta
```

Force specific packages to be treated as changed (and their dependents).

## Release all packages

```bash
uvr release --all-packages
```

Treats all packages as changed regardless of what files were modified.

## Python version

The Python version for CI builds is configured in `[tool.uvr.config]` in your root `pyproject.toml`. See [Reference](08-reference.md) for all configuration keys.
