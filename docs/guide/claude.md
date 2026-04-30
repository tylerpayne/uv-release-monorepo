# Release with Claude

`uvr` ships with a Claude Code skill that handles the entire release flow interactively.

## Install the skill

```bash
uvr skill install
```

This copies the `/release` skill into your project's `.claude/skills/` directory.

## Use it

```
/release
```

Claude will:

1. **Branch.** Create a release branch if you are on main.
2. **Preview.** Run `uvr release --dry-run` and show what changed.
3. **Bump.** Ask if any packages need a minor or major bump instead of patch.
4. **Review.** Audit public API against docstrings and docs.
5. **Release notes.** Draft user-facing notes for your approval.
6. **Dispatch.** Commit, push, and run `uvr release`.
7. **Monitor.** Watch the workflow and handle failures.
8. **Merge.** Merge the release branch back to main.

## What Claude handles

- **Version suggestions.** Presents what changed and asks whether patch is appropriate.
- **API review.** Checks that docstrings and docs match actual exports.
- **Release notes.** Writes prose (not commit dumps) using [Keep a Changelog](https://keepachangelog.com/) format.
- **Failure recovery.** Reads CI logs and uses `--skip-to` / `--reuse-run` to resume.

## Upgrade the skill

```bash
uvr skill install --upgrade
```

Three-way merges the latest skill template while preserving your customizations.
