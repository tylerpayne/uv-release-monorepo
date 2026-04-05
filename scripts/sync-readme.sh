#!/bin/bash
# Sync package README to root README
# Replaces everything before "## Repository Structure" in root README
# with the contents of packages/uv-release-monorepo/README.md

set -e

ROOT_README="README.md"
PKG_README="packages/uv-release-monorepo/README.md"
MARKER="## Repository Structure"

if [[ ! -f "$PKG_README" ]]; then
    echo "Error: $PKG_README not found"
    exit 1
fi

if [[ ! -f "$ROOT_README" ]]; then
    echo "Error: $ROOT_README not found"
    exit 1
fi

# Extract everything from marker onwards in root README
REPO_SECTION=$(sed -n "/$MARKER/,\$p" "$ROOT_README")

if [[ -z "$REPO_SECTION" ]]; then
    echo "Error: '$MARKER' not found in $ROOT_README"
    exit 1
fi

# Combine package README + repo section, rewriting guide link for root context
# Insert badges after the title line for the root README
{
    head -1 "$PKG_README"
    echo ""
    echo '[![Docs](https://github.com/tylerpayne/uv-release-monorepo/actions/workflows/docs.yml/badge.svg)](https://tylerpayne.github.io/uv-release-monorepo/)'
    echo '[![PyPI](https://img.shields.io/pypi/v/uv-release-monorepo)](https://pypi.org/project/uv-release-monorepo/)'
    tail -n +2 "$PKG_README" | sed 's|(../../docs/guide.md)|(docs/guide.md)|g'
    echo ""
    echo "$REPO_SECTION"
} > "$ROOT_README"

# Stage the updated root README if it changed
git add "$ROOT_README"
