# `uvr bump`

Bump package versions in the workspace. This changes `pyproject.toml` versions, pins internal dependencies, syncs the lockfile, and commits the result.

```bash
uvr bump --minor              # bump all packages
uvr bump --packages foo --rc  # bump one package to rc
```

## Bump types

Exactly one bump type is required.

| Flag | Effect | Example |
|------|--------|---------|
| `--major` | Next major, dev track | `1.2.3.dev0` to `2.0.0.dev0` |
| `--minor` | Next minor, dev track | `1.2.3.dev0` to `1.3.0.dev0` |
| `--patch` | Next patch, dev track | `1.2.3.dev0` to `1.2.4.dev0` |
| `--alpha` | Enter or advance alpha | `1.2.3.dev0` to `1.2.3a0.dev0` |
| `--beta` | Enter or advance beta | `1.2.3a0.dev0` to `1.2.3b0.dev0` |
| `--rc` | Enter or advance rc | `1.2.3b0.dev0` to `1.2.3rc0.dev0` |
| `--post` | Enter post-release track | `1.2.3` to `1.2.3.post0.dev0` |
| `--dev` | Increment dev number | `1.2.3.dev0` to `1.2.3.dev1` |
| `--stable` | Strip dev/pre suffixes | `1.2.3a2.dev0` to `1.2.3` |

Not all transitions are valid. For example, you cannot bump from beta back to alpha, or from a pre-release into the post track. Invalid transitions raise an error.

## Scope flags

| Flag | Description |
|------|-------------|
| `--all` | Bump all packages (default when no scope given) |
| `--packages PKG...` | Bump only the named packages |

`--all` and `--packages` are mutually exclusive.

## Options

| Flag | Description |
|------|-------------|
| `--no-pin` | Skip internal dependency pinning |
| `--force` | Skip the changed-package guard |

## What it does

1. Computes the new version for each target package
2. Writes the new version to each package's `pyproject.toml`
3. Pins internal dependency lower bounds to match the new versions
4. Runs `uv sync` to update the lockfile
5. Commits all changes with a `chore: bump to next dev versions` message

## Common patterns

```bash
# Prepare a minor release for all packages
uvr bump --minor

# Enter an alpha pre-release cycle for one package
uvr bump --packages my-lib --alpha

# Finalize a pre-release cycle into a stable version
uvr bump --stable

# Bump just the dev number (for dev releases)
uvr bump --dev
```

See `pre-releases.md` for the full alpha, beta, rc, stable workflow. See `post-releases.md` for post-release bumps.
