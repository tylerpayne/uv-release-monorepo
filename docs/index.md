---
layout: home

hero:
  name: uvr
  tagline: <span>Release management for <a href="https://github.com/astral-sh/uv">uv</a> workspaces.</span>
  actions:
    - theme: brand
      text: Get Started
      link: /guide/getting-started
    - theme: alt
      text: Go Under the Hood
      link: /internals/architecture

features:
  - title: Scaffold
    details: "<code class=\"brand-code\">uvr workflow install</code><br>Generate a complete release workflow in one command. Runner matrices, PyPI publishing, and hooks built in."
    link: /guide/getting-started#scaffold-the-release-workflow
  - title: Version
    details: "<code class=\"brand-code\">uvr version</code><br>Bump versions without breaking internal dependencies. Downstream pins update automatically."
    link: /guide/versions
  - title: Release
    details: "<code class=\"brand-code\">uvr release</code><br>Release with confidence. Catch errors before dispatch, only rebuild what changed, and recover from failures without starting over."
    link: /guide/releasing
  - title: Claude
    details: "<code class=\"brand-code\">/release</code><br>Ship interactively. Claude handles branching, release notes, dispatch, and failure recovery."
    link: /guide/claude
---

## Quick Start

You have a uv workspace with three packages. `auth` is a leaf. `api` depends on it. `cli` hasn't changed.

Install uvr as a dev dependency.

```bash
uv add --dev uv-release
```

Scaffold the release workflow.

```bash
uvr workflow install
```

Plan, confirm, and dispatch.

```bash
uvr release
```

```
Packages
--------
  files changed     auth    0.2.0.dev0
  files changed     api     0.1.1.dev0
  unchanged         cli     1.0.0

Pipeline
--------
  run     validate
  run     build
  run     release
  run     publish
  run     bump

Proceed? [y/N]
```

Change detection, topological build ordering, GitHub releases, PyPI publishing, and version bumping. All planned locally before anything touches CI. See the [setup guide](/guide/getting-started) for the full walkthrough.
