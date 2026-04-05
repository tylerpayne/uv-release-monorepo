# Managing Versions

## How versions work

Every package carries a [`.devN`](https://peps.python.org/pep-0440/#developmental-releases) suffix between releases. <code class="brand-code">uvr release</code> strips `.devN` to produce the published version. After release, CI bumps to the next patch `.dev0`.

```
1.3.0.dev0  →  release  →  1.3.0  →  CI bumps  →  1.3.1.dev0
```

## Bump changed packages

```bash
uvr bump --minor
```

By default, <code class="brand-code">uvr bump</code> only targets packages with changes since their last release. It writes new versions to `pyproject.toml`, updates internal dependency pins in downstream packages, and syncs the lockfile.

## Bump specific packages

```bash
uvr bump --packages pkg-alpha pkg-beta --major
```

If other packages also have unreleased changes, <code class="brand-code">uvr</code> errors to prevent accidental partial bumps. Override with `--force`.

```bash
uvr bump --packages pkg-alpha --major --force
```

## Skip dependency pinning

```bash
uvr bump --packages pkg-alpha --minor --no-pin
```

By default, bumping a package updates `>=` pins in downstream dependents. The `--no-pin` flag skips this.

## Bump types

| Flag | Example | Description |
|---|---|---|
| `--major` | `1.2.3.dev0` → `2.0.0.dev0` | Next major version |
| `--minor` | `1.2.3.dev0` → `1.3.0.dev0` | Next minor version |
| `--patch` | `1.2.3.dev0` → `1.2.4.dev0` | Next patch version |
| `--alpha` | `1.3.0.dev0` → `1.3.0a0.dev0` | Enter alpha [pre-release](https://peps.python.org/pep-0440/#pre-releases) cycle |
| `--beta` | `1.3.0a2.dev0` → `1.3.0b0.dev0` | Enter beta pre-release cycle |
| `--rc` | `1.3.0b1.dev0` → `1.3.0rc0.dev0` | Enter release candidate cycle |
| `--post` | `1.3.0.dev0` → `1.3.0.post0.dev0` | Enter [post-release](https://peps.python.org/pep-0440/#post-releases) cycle |
| `--dev` | `1.3.0.dev0` → `1.3.0.dev1` | Increment the dev number |
| `--stable` | `1.3.0a2.dev0` → `1.3.0.dev0` | Strip pre-release markers |

Repeating the same pre-release type increments it. `--alpha` twice goes `1.0.0a0.dev0` → `1.0.0a1.dev0`.

## Pre-release workflow

```bash
uvr bump --minor                  # 1.3.0.dev0
uvr bump --alpha                  # 1.3.0a0.dev0
uvr release                       # publishes 1.3.0a0, CI bumps to 1.3.0a1.dev0
uvr bump --alpha                  # 1.3.0a2.dev0
uvr release                       # publishes 1.3.0a2, CI bumps to 1.3.0a3.dev0
uvr bump --beta                   # 1.3.0b0.dev0
uvr release                       # publishes 1.3.0b0, CI bumps to 1.3.0b1.dev0
uvr bump --stable                 # 1.3.0.dev0
uvr release                       # publishes 1.3.0, CI bumps to 1.3.1.dev0
```

## Tag formats

<code class="brand-code">uvr</code> creates two kinds of tags.

**Release tags** mark published versions. Format `{package}/v{version}`.

```
pkg-alpha/v1.3.0
```

**Baseline tags** mark where the next dev cycle begins. Format `{package}/v{version}-base`.

```
pkg-alpha/v1.3.1.dev0-base
```

Change detection compares HEAD against the baseline tag. If no baseline exists, the package is treated as new.

---

**Under the hood.** [Bump](../under-the-hood/02-bump.md) | [Change Detection](../under-the-hood/01-change-detection.md)
