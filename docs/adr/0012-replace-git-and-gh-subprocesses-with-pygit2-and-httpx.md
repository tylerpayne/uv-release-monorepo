# Replace Git And Gh Subprocesses With Pygit2 And Httpx

* Status: accepted
* Date: 2026-03-27

## Context and Problem Statement

In large workspaces, `uvr release` was taking many seconds to generate a plan because each git query and GitHub API call spawned a subprocess (`git`, `gh`). How can we reduce planning latency without changing the plan output?

## Decision Drivers

* Planning must be fast even in workspaces with many packages and long histories
* The solution must produce identical plans — this is a pure performance change
* Library choice should be well-maintained and available on common platforms

## Considered Options

* pygit2 (libgit2 bindings) + httpx (async HTTP for GitHub API)
* dulwich (pure Python git) + httpx
* GitPython (subprocess wrapper around git) + httpx

| Criterion | pygit2 + httpx | dulwich + httpx | GitPython + httpx |
|---|---|---|---|
| Git operation speed | Fast — C library (libgit2) | Moderate — pure Python | Same as subprocess — wraps `git` CLI |
| Diff/log without subprocess | Yes — in-process | Yes — in-process | No — still shells out |
| Platform availability | Pre-built wheels for all major platforms | Pure Python, runs anywhere | Requires `git` on PATH |
| API maturity | Stable, well-maintained | Stable, but lower-level API | Stable, widely used |
| Install size | ~5 MB (binary wheel) | ~1 MB | Minimal (git already present) |

## Decision Outcome

Chosen option: "pygit2 + httpx", because pygit2 eliminates subprocess overhead for git operations via in-process libgit2 calls, and httpx replaces `gh` subprocess calls with direct HTTP requests. GitPython was rejected because it still shells out to `git`, which doesn't solve the latency problem. dulwich was a viable alternative but pygit2's C-backed performance is better suited for the diff-heavy operations in change detection.

### Positive Consequences

* Planning is significantly faster — no subprocess spawning for git or GitHub API calls
* httpx enables future parallelization of GitHub API requests
* In-process git access enables more granular diff operations without parsing CLI output

### Negative Consequences

* pygit2 adds a binary dependency (~5 MB wheel, bundles libgit2) — pre-built wheels cover all major platforms but niche architectures (s390x, musl ppc64le) require building from source with libgit2 headers
* Two new runtime dependencies to keep updated (pygit2, httpx)
* Contributors need pygit2 installed locally for development, slightly raising the setup bar

### Subsequent Changes

The httpx migration was not completed. GitHub API calls still use `gh` subprocess. Some git operations (`commit_log`, `diff_stats`) still use `git` subprocess. Core tag and ref operations use pygit2.
