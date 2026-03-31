# uv-release-monorepo

The missing CI release orchestrator for [uv](https://github.com/astral-sh/uv) workspaces. Rebuilds only what changed, creates one GitHub release per package, handles version bumping.

## Quick Start

```bash
# Install as a dev dependency
uv add --dev uv-release-monorepo

# Generate .github/workflows/release.yml
uvr workflow init

# Preview what would be released
uvr release --dry-run

# Plan + dispatch to GitHub Actions
uvr release
```

## Configuration

```bash
# Add a cross-platform build runner
uvr workflow runners my-pkg --add macos-14

# Check release.yml against the schema
uvr workflow validate
```

```toml
# pyproject.toml — control which packages are released
[tool.uvr.config]
# only release these (optional)
include = ["pkg-alpha", "pkg-beta"]  
# skip these (optional) 
exclude = ["pkg-internal"]           
```

Add custom jobs (tests, linting, PyPI publish, notifications) by editing `release.yml` directly, or extend the pipeline with Python hooks by subclassing `ReleaseHook` in `uvr_hooks.py`. See the [User Guide](docs/user-guide/README.md) for details.

## Example

```bash
# Start from main
git checkout -b release/my-feature

# Enter alpha pre-release cycle
uvr bump --package my-pkg --alpha

# Make changes, commit, push

# Release alpha
uvr release --pre

# Iterate — fix bugs

# Release next alpha
uvr release --pre

# No more bugs, release stable
uvr release

# Merge back to main
git checkout main
git merge --no-ff release/my-feature
git push
```

## Claude Skill

Let Claude release for you.

```bash
uvr skill init
```

```bash
# Claude or your favorite SKILL.md-supporting agent
claude

> /release [--dev|--pre|--post]
```

## Consuming Releases

Haven't published to PyPi? No problem, install your packages directly from GitHub releases.

```bash
# Install from GitHub releases
uvr install myorg/myrepo/my-pkg@0.1.2

# Download wheels only
uvr download myorg/myrepo/my-pkg
```

## Documentation

- **[User Guide](docs/user-guide/README.md)** — setup, releasing, custom jobs, troubleshooting, command reference
- **[Under the Hood](docs/under-the-hood/README.md)** — change detection, dependency pinning, build matrix, workflow model
