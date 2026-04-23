# `uvr release --dry-run`

Preview what would be released without making changes.

```bash
uvr release --dry-run
```

Shows which packages have changed since their last release tag, their current versions, and whether they changed directly or transitively (via dependency updates).

## Flags

| Flag | Description |
|------|-------------|
| `--all-packages` | Show all packages as changed |
| `--packages PKG...` | Show specific packages |
