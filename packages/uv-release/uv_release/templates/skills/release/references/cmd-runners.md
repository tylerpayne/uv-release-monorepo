# `uvr configure runners`

Manage per-package build runners. By default, all packages build on `ubuntu-latest`. Use this to add platform-specific runners for cross-platform wheel builds.

```bash
uvr configure runners                                             # show all package runner configs
uvr configure runners --package my-pkg --add macos-latest         # add a runner
uvr configure runners --package my-pkg --remove macos-latest      # remove a runner
uvr configure runners --package my-pkg --clear                    # reset to default
```

## Flags

| Flag | Description |
|------|-------------|
| `--package PKG` | Package to configure |
| `--add LABEL [...]` | Add runner labels to the package |
| `--remove LABEL [...]` | Remove runner labels from the package |
| `--clear` | Remove all custom runners for the package (revert to default) |

Runner configuration is stored in `[tool.uvr.runners]` in the root `pyproject.toml`. The build job's matrix expands to one job per unique runner, and each runner builds all packages assigned to it.
