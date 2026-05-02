# Getting Started

## Install

```bash
uv add --dev uv-release
```

## Prerequisites

`uvr` works with uv workspace monorepos. Your root `pyproject.toml` must define workspace members.

```toml
[tool.uv.workspace]
members = ["packages/*"]
```

You also need the [GitHub CLI](https://cli.github.com/) (`gh`) authenticated. `uvr` uses it to create releases, download artifacts, and dispatch workflows. It always prompts for confirmation before committing, pushing, or dispatching on your behalf.

## Scaffold the release workflow

```bash
uvr workflow install
```

This writes `.github/workflows/release.yml` from a bundled template. Commit and push it.

```bash
git add .github/workflows/release.yml
git commit -m "chore: add release workflow"
git push
```

The workflow can be customized and upgraded over time. See [Configuration](configuration.md#workflow-management) for validation and upgrade flows.

## Check workspace status

```bash
uvr status
```

```
Packages
--------
  STATUS         PACKAGE    VERSION      DIFF FROM
  files changed  pkg-alpha  0.2.0.dev0   pkg-alpha/v0.1.0.dev0-base
  unchanged      pkg-beta   0.1.2.dev0   pkg-beta/v0.1.2.dev0-base
```

## Your first release

You can also release interactively with the [Claude Code skill](claude.md).

Preview the plan without making changes.

```bash
uvr release --dry-run
```

When ready, release for real.

```bash
uvr release
```

This generates a release plan locally, commits release versions, pushes, and dispatches to GitHub Actions. CI then builds, creates GitHub releases with wheels, publishes to configured indexes, and bumps versions to the next `.dev0`.

## Next steps

To release a minor or major version instead of patch, bump first. See [Managing Versions](versions.md) for the full version lifecycle.

```bash
uvr version --bump minor
uvr release
```
