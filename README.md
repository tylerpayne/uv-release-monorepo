# uvr

[![Docs](https://github.com/tylerpayne/uvr/actions/workflows/docs.yml/badge.svg)](https://tylerpayne.github.io/uvr/)
[![PyPI](https://img.shields.io/pypi/v/uv-release)](https://pypi.org/project/uv-release/)

Release management for [uv](https://github.com/astral-sh/uv) workspaces.

## Install once

```bash
uv add --dev uv-release
uvr workflow install
```

## Release with confidence

```bash
uvr release
```

```
Packages
--------
PACKAGE       RELEASE    NEXT       
my-core       0.35.1     0.35.2.dev0
my-extra      0.42.3     0.42.4.dev0

Pipeline
--------
  validate
  check
  build
    ubuntu-latest
      targets:
        my-core
        my-extra
    windows-latest
      deps:
        my-core
      targets:
        my-extra
    macos-latest
      deps:
        my-core
      targets:
        my-extra
  release
    my-core  my-core/v0.35.1
    my-extra my-extra/v0.42.3
  publish
    my-core  pypi
    my-extra pypi
  bump
    my-core  0.35.2.dev0
    my-extra 0.42.4.dev0

Release notes
-------------
  my-core:
    b2075ab fix: bug
  my-extra:
    b38h3kl fix: bug 

Proceed? (y/N):
```

## Documentation

- **[User Guide](https://tylerpayne.github.io/uvr/user-guide/01-getting-started)**
- **[Under the Hood](https://tylerpayne.github.io/uvr/under-the-hood/architecture)**
