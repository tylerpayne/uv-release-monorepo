# Pre-releases

Pre-releases let you publish alpha, beta, or release candidate versions for testing before a stable release. They follow [PEP 440](https://peps.python.org/pep-0440/#pre-releases) versioning.

## Usage

Use `uvr version` to enter a pre-release cycle, then `uvr release` to publish:

```bash
uvr version --all-packages --promote alpha    # enter alpha cycle → 1.2.3a0.dev0
uvr release                  # publishes 1.2.3a0, bumps to 1.2.3a1.dev0
```

## How it works

1. `uvr version --promote alpha` (or `--promote beta`, `--promote rc`) sets each package's version to `X.Y.Za0.dev0`
2. `uvr release` strips `.devN` and publishes `X.Y.Za0`
3. After release, the pyproject.toml version is bumped to `X.Y.Za1.dev0` (dev toward the next pre-release of the same kind)
4. Subsequent `uvr release` calls publish `X.Y.Za1`, `X.Y.Za2`, etc.

To advance to the next kind (alpha → beta → rc), promote again:

```bash
uvr version --all-packages --promote beta     # advance to beta → 1.2.3b0.dev0
uvr release                  # publishes 1.2.3b0
```

## Version ordering

Pre-releases sort before the stable release:

```
1.0.1.dev0 < 1.0.1a0 < 1.0.1a1 < 1.0.1b0 < 1.0.1rc0 < 1.0.1
```

## Example workflow

```bash
# Enter alpha cycle
uvr version --all-packages --promote alpha
# pyproject.toml: 1.2.3a0.dev0

uvr release
# → publishes 1.2.3a0
# → bumps to 1.2.3a1.dev0

# Second alpha (after more changes)
uvr release
# → publishes 1.2.3a1
# → bumps to 1.2.3a2.dev0

# Advance to release candidate
uvr version --all-packages --promote rc
# pyproject.toml: 1.2.3rc0.dev0

uvr release
# → publishes 1.2.3rc0

# Final release
uvr version --all-packages --promote final
# pyproject.toml: 1.2.3.dev0

uvr release
# → publishes 1.2.3
# → bumps to 1.2.4.dev0
```

## Kind advancement rules

`uvr version` enforces that pre-release kinds only move forward:

| Current | Allowed | Blocked |
|---|---|---|
| alpha | `--promote alpha`, `--promote beta`, `--promote rc` | — |
| beta | `--promote beta`, `--promote rc` | `--promote alpha` (downgrade) |
| rc | `--promote rc` | `--promote alpha`, `--promote beta` (downgrade) |

## Merging

**DO NOT merge pre-release branches back to main.** Stay on the branch through the entire cycle (alpha → beta → rc → stable) and merge only after the stable release.

After a pre-release, finalize bumps the pyproject.toml version to something like `1.2.3a1.dev0`. If you merged that to main, main's version would be an intermediate pre-release dev version — confusing and unnecessary.

Keep iterating on the branch until you're ready for the stable release:

```bash
uvr version --all-packages --promote alpha && uvr release   # 1.2.3a0 — stay on branch
uvr version --all-packages --promote rc && uvr release      # 1.2.3rc0 — stay on branch
uvr version --all-packages --promote final && uvr release   # 1.2.3 — now merge to main
```

Merge to main only after the stable release.

## Tag format

Pre-release tags follow the same pattern as stable releases:

```
my-pkg/v1.2.3a0
my-pkg/v1.2.3rc1
```
