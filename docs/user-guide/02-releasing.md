# Releasing Packages

## The standard release

```bash
uvr release
```

<code class="brand-code">uvr release</code> detects what changed, sets release versions, commits, and dispatches a plan to GitHub Actions. CI then builds, creates GitHub releases with wheels, publishes to configured indexes, and bumps to the next dev version. See [Architecture](../under-the-hood/architecture.md) for the full pipeline.

## Preview without releasing

```bash
uvr release --dry-run
```

Runs all detection and planning logic but makes no changes.

## Export plan as JSON

```bash
uvr release --json
```

## Bump versions inline

```bash
uvr release --bump minor
```

Bumps all changed packages before generating the plan. Equivalent to `uvr bump --minor` followed by `uvr release` in a single command. Available types. `alpha`, `beta`, `rc`, `post`, `dev`, `stable`, `minor`, `major`, `patch`.

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

## Allow a dirty working tree

```bash
uvr release --allow-dirty
```

Turns clean-tree and remote-match checks into warnings instead of errors.

## Rebuild all packages

```bash
uvr release --rebuild-all
```

## Set the Python version for CI

```bash
uvr release --python 3.11
```

Defaults to `3.12`.
