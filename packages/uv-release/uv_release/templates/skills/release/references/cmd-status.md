# `uvr status`

Show which packages have changed since their last release baseline.

```bash
uvr status
```

Displays each package's name, version, change reason (files changed, initial release, dependency changed, or unchanged), and the baseline tag it was diffed against.

## Flags

| Flag | Description |
|------|-------------|
| `--all-packages` | Show all packages as changed |
| `--packages PKG...` | Show specific packages |
