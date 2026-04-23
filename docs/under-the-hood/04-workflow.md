# <code class="brand-code">uvr workflow</code>: A CI Template You Never Debug

<code class="brand-code">uvr</code>'s workflow YAML never changes when your repo structure changes. Add packages, change dependency graphs, modify build matrices. The YAML stays the same. All intelligence is in the [plan JSON](architecture.md), and the workflow just reads it.

```yaml
# This drives the entire build matrix.
# Works for 1 package or 100, 1 runner or 10.
strategy:
  matrix:
    runner: ${{ fromJSON(inputs.plan).build_matrix }}
```

## Workflow management

<code class="brand-code">uvr workflow init</code> copies a bundled YAML template into your repository. <code class="brand-code">uvr workflow validate</code> parses the YAML and checks for required jobs.

## Validation

Validation checks two things.

1. The five required jobs exist (`validate`, `build`, `release`, `publish`, `bump`).
2. Whether the file differs from the bundled template. If it does, a warning is emitted.

## Pipeline enforcement

Core jobs have mandatory `needs` dependencies.

```
validate -> build -> release -> publish -> bump
```

## Custom workflow jobs

Add your own jobs to `release.yml` by editing the YAML directly.

```yaml
pre-build:
  needs: [validate]
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: uv run poe check
    - run: uv run poe test
```

Custom jobs survive <code class="brand-code">uvr workflow init --upgrade</code>. The three-way merge preserves user additions.

## Python hooks

For injecting data into the plan before it reaches CI. The default hooks file is `uvr_hooks.py` with a default class named `Hooks`.

```python
from uv_release import Hooks


class MyHooks(Hooks):
    def post_plan(self, workspace, intent, plan):
        # Modify the plan before it is dispatched
        return plan
```

**Local hooks** run on your machine during <code class="brand-code">uvr release</code>. These are `pre_plan` and `post_plan`.

**CI hooks** run inside the workflow. These are `pre_build`, `post_build`, `pre_release`, `post_release`, `pre_publish`, `post_publish`, `pre_bump`, and `post_bump`.

## Init, validate, and upgrade

### <code class="brand-code">uvr workflow init</code>

Generates `release.yml` from defaults. Checks that the CWD is a git repo with `[tool.uv.workspace].members`. Refuses to overwrite without `--force`.

### <code class="brand-code">uvr workflow validate</code>

Validates the existing YAML against the template. Checks for required jobs and reports if the file differs from the template. Never modifies the file.

### <code class="brand-code">uvr workflow init --upgrade</code>

Performs a three-way merge between the merge base (defaults from the <code class="brand-code">uvr</code> version that generated the file), the current file (your customized version), and the new defaults (from the current <code class="brand-code">uvr</code> version).

Your customizations are preserved. Conflicts open in your editor. Use `--base-only` to inspect merge bases without merging.
