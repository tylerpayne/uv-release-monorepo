# <code class="brand-code">uvr bump</code>: Automatic Dependency Pinning

<code class="brand-code">uvr bump</code> manages versions and pins internal dependencies automatically. When you bump pkg-alpha to `0.1.5`, every workspace package that depends on alpha gets its constraint updated.

```
pkg-beta/pyproject.toml
  pkg-alpha>=0.1.0  →  pkg-alpha>=0.1.5

pkg-gamma/pyproject.toml
  pkg-beta>=0.1.0   →  pkg-beta>=0.2.0

pkg-delta/pyproject.toml
  pkg-alpha>=0.1.0  →  pkg-alpha>=0.1.5
```

No manual auditing. No stale constraints shipping broken wheels. See [PEP 440 version specifiers](https://peps.python.org/pep-0440/#version-specifiers) for constraint syntax.

## How pins are computed

The planner builds a `published_versions` map for every workspace package.

- **Changed packages** publish at their release version. `0.1.5.dev0` strips to `0.1.5`.
- **Unchanged packages** use the version from their last release tag. `pkg-alpha/v0.1.4` gives `0.1.4`.

Every internal dep constraint is rewritten to `>=published_version`. Pins cover `[project].dependencies`, `[project].optional-dependencies`, and `[dependency-groups]`. `[build-system].requires` is **not** pinned. Build-time deps are resolved through the [layered build system](03-build.md) instead.

## Pin detection without side effects

Pin detection is pure. No files are modified during plan generation. If pins need updating, <code class="brand-code">uvr release</code> shows the pending changes.

```
Dependency pins
  pkg-beta/pyproject.toml
    pkg-alpha>=0.1.0  →  pkg-alpha>=0.1.5
  pkg-gamma/pyproject.toml
    pkg-beta>=0.1.0   →  pkg-beta>=0.2.0
```

On confirmation, <code class="brand-code">uvr</code> writes the pins and instructs you to commit and re-run.

```
Commit pin updates before dispatching:
  git add -A && git commit -m 'chore: update dependency pins' && git push
  uvr release
```

The second run detects no pending changes and proceeds to dispatch.

## Post-release pinning

After CI builds and publishes, the bump phase pins internal deps to the just-published versions. This ensures `pyproject.toml` constraints stay satisfiable during development.

```
uvr pin-deps --path packages/pkg-beta/pyproject.toml pkg-alpha>=0.1.5
uvr pin-deps --path packages/pkg-gamma/pyproject.toml pkg-beta>=0.2.0
```

These commands are embedded in the `ReleasePlan` JSON. Pins only land in the repo if the build succeeds.

## Version management

Use <code class="brand-code">uvr bump</code> to set the version you intend to release.

```bash
uvr bump --minor             # bump changed packages to next minor
uvr bump --alpha                 # enter alpha pre-release cycle
uvr bump --rc                    # promote alpha → release candidate
uvr bump --stable                # exit pre-release → stable
uvr bump --packages my-pkg --patch  # bump specific package(s)
```

After every release, CI bumps the patch number and appends [`.dev0`](https://peps.python.org/pep-0440/#developmental-releases).

```
1.0.1      (released)   →   1.0.2.dev0   (next dev version)
1.0.1a0    (released)   →   1.0.1a1.dev0 (next pre-release dev)
1.0.0.post0 (released)  →   1.0.0.post1.dev0 (next post-release dev)
```

On release, `.dev0` is stripped automatically.

### The version lifecycle

```
commit A  ← pkg-alpha/v0.1.5              (release tag)
commit B  ← pkg-alpha/v0.1.6.dev0-base    (baseline; pyproject.toml bumped to 0.1.6.dev0)
commits   … normal development …
commit C  ← pkg-alpha/v0.1.6              (release tag)
commit D  ← pkg-alpha/v0.1.7.dev0-base    (baseline; pyproject.toml bumped to 0.1.7.dev0)
```

The `-base` tags serve as diff baselines for [change detection](01-change-detection.md).
