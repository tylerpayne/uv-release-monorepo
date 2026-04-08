# uvr

[![Docs](https://github.com/tylerpayne/uvr/actions/workflows/docs.yml/badge.svg)](https://tylerpayne.github.io/uvr/)
[![PyPI](https://img.shields.io/pypi/v/uv-release)](https://pypi.org/project/uv-release/)

Release management for [uv](https://github.com/astral-sh/uv) workspaces.

## Install once

```bash
uv add --dev uv-release
uvr workflow init
```

## Release with confidence

```bash
uvr release
```

Detects changes, pins dependencies, and plans a topologically ordered build, publish, and bump. Validates everything locally before dispatch. Version conflicts, stale pins, and dirty working trees are caught on your machine, not in CI.


```
Planning
--------
  |##########| Discovered 3 packages (9ms)
  |----------| Resolved 3 baselines (57us)
  |#####-----| Detected 2 changed, 1 unchanged (4ms)
  |###-------| Computed versions for 2 packages (2ms)
  |----------| Generated 2 release notes (625ns)
  Planned 2 releases in 16ms

Packages
--------
  STATUS     PACKAGE  VERSION      PREVIOUS  CHANGES  COMMITS
  changed    my-auth     0.2.0.dev0   0.1.0     3        2
  changed    my-api      0.1.1.dev0   0.1.0     1        1
  unchanged  my-cli      1.0.0        1.0.0     -        -

Pipeline
--------
  run   uvr-build
          [ubuntu-latest]
            layer 0
              my-auth  0.2.0
            layer 1
              my-api   0.1.1
  run   uvr-release
          my-auth/v0.2.0
          my-api/v0.1.1
  run   uvr-publish
          my-auth → pypi
          my-api  → pypi
  run   uvr-bump
          my-auth → 0.2.1.dev0
          my-api  → 0.1.2.dev0

Dispatch release? [y/N]
```

## Documentation

- **[User Guide](https://tylerpayne.github.io/uvr/user-guide/01-getting-started)**
- **[Under the Hood](https://tylerpayne.github.io/uvr/under-the-hood/architecture)**
