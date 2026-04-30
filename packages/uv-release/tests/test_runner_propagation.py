"""Tests for runner propagation in multi-runner monorepos.

Uses the _compute_effective_runners function directly with a topology
modeled after a monorepo with mixed platform requirements.

Topology:
  core           (linux)          no deps
  net-utils      (linux)          no deps
  build-tools    (linux)          no deps
  emulator       (windows, linux, macos, linux-arm64)  build-dep: build-tools
  img-tools      (linux)          dep: core
  distro-a       (linux, macos)   build-deps: img-tools, core, emulator, net-utils
  distro-b       (linux, macos)   build-deps: img-tools, core, emulator, net-utils
  agent          (linux, macos)   dep: core, distro-a; build-deps: img-tools, core, distro-a, emulator, net-utils
  app            (linux, macos)   dep: core, agent; build-deps: img-tools, core, agent, distro-a, emulator, net-utils
"""

from __future__ import annotations

from uv_release.dependencies.build.build_job import _compute_effective_runners
from uv_release.dependencies.build.build_packages import BuildPackages
from uv_release.dependencies.config.uvr_runners import UvrRunners
from uv_release.types.dependency import Dependency
from uv_release.types.package import Package
from uv_release.types.version import Version

_d = Dependency.parse
_V = Version.parse("0.1.0.dev0")

LINUX = ["self-hosted", "linux", "x64"]
MACOS = ["self-hosted", "macos", "arm64"]
WINDOWS = ["self-hosted", "x64", "windows"]
LINUX_ARM = ["self-hosted", "linux", "arm64"]

PACKAGES: dict[str, Package] = {
    "core": Package(
        name="core",
        path="packages/core",
        version=_V,
        dependencies=[],
        build_dependencies=[],
    ),
    "net-utils": Package(
        name="net-utils",
        path="packages/net-utils",
        version=_V,
        dependencies=[],
        build_dependencies=[],
    ),
    "build-tools": Package(
        name="build-tools",
        path="packages/build-tools",
        version=_V,
        dependencies=[],
        build_dependencies=[],
    ),
    "emulator": Package(
        name="emulator",
        path="packages/emulator",
        version=_V,
        dependencies=[],
        build_dependencies=[_d("build-tools")],
    ),
    "img-tools": Package(
        name="img-tools",
        path="packages/img-tools",
        version=_V,
        dependencies=[_d("core")],
        build_dependencies=[],
    ),
    "distro-a": Package(
        name="distro-a",
        path="packages/distro-a",
        version=_V,
        dependencies=[_d("core")],
        build_dependencies=[
            _d("img-tools"),
            _d("core"),
            _d("emulator"),
            _d("net-utils"),
        ],
    ),
    "distro-b": Package(
        name="distro-b",
        path="packages/distro-b",
        version=_V,
        dependencies=[_d("core")],
        build_dependencies=[
            _d("img-tools"),
            _d("core"),
            _d("emulator"),
            _d("net-utils"),
        ],
    ),
    "agent": Package(
        name="agent",
        path="packages/agent",
        version=_V,
        dependencies=[_d("core"), _d("distro-a")],
        build_dependencies=[
            _d("img-tools"),
            _d("core"),
            _d("distro-a"),
            _d("emulator"),
            _d("net-utils"),
        ],
    ),
    "app": Package(
        name="app",
        path="packages/app",
        version=_V,
        dependencies=[_d("core"), _d("agent")],
        build_dependencies=[
            _d("img-tools"),
            _d("core"),
            _d("agent"),
            _d("distro-a"),
            _d("emulator"),
            _d("net-utils"),
        ],
    ),
}

RUNNERS = UvrRunners(
    items={
        "core": [LINUX],
        "net-utils": [LINUX],
        "build-tools": [LINUX],
        "emulator": [WINDOWS, LINUX, MACOS, LINUX_ARM],
        "img-tools": [LINUX],
        "distro-a": [LINUX, MACOS],
        "distro-b": [LINUX, MACOS],
        "agent": [LINUX, MACOS],
        "app": [LINUX, MACOS],
    }
)

BUILD_PACKAGES = BuildPackages(items=PACKAGES)


class TestMonorepoRunnerPropagation:
    """Verify runner propagation with a realistic multi-platform monorepo."""

    def _effective(self) -> dict[str, list[list[str]]]:
        return _compute_effective_runners(PACKAGES, RUNNERS, BUILD_PACKAGES)

    def test_distro_does_not_run_on_windows(self) -> None:
        """distro-b only runs on linux and macos, not windows."""
        eff = self._effective()
        assert WINDOWS not in eff.get("distro-b", [])

    def test_distro_runs_on_linux_and_macos(self) -> None:
        eff = self._effective()
        runners = eff.get("distro-b", [])
        assert LINUX in runners
        assert MACOS in runners

    def test_emulator_runs_on_all_four(self) -> None:
        """emulator has its own 4 runners."""
        eff = self._effective()
        runners = eff.get("emulator", [])
        assert WINDOWS in runners
        assert LINUX in runners
        assert MACOS in runners
        assert LINUX_ARM in runners

    def test_build_tools_inherits_from_emulator(self) -> None:
        """build-tools is a build dep of emulator, inherits emulator's runners."""
        eff = self._effective()
        runners = eff.get("build-tools", [])
        assert WINDOWS in runners
        assert LINUX in runners
        assert MACOS in runners

    def test_net_utils_inherits_from_dependents(self) -> None:
        """net-utils is a build dep of distro-a, distro-b, agent, app."""
        eff = self._effective()
        runners = eff.get("net-utils", [])
        assert LINUX in runners
        assert MACOS in runners

    def test_net_utils_does_not_inherit_windows(self) -> None:
        """No package that depends on net-utils runs on windows."""
        eff = self._effective()
        assert WINDOWS not in eff.get("net-utils", [])

    def test_core_inherits_from_all_dependents(self) -> None:
        eff = self._effective()
        runners = eff.get("core", [])
        assert LINUX in runners
        assert MACOS in runners

    def test_leaf_only_on_own_runners(self) -> None:
        """app (a leaf) should only run on its own linux and macos."""
        eff = self._effective()
        runners = eff.get("app", [])
        assert WINDOWS not in runners
        assert LINUX_ARM not in runners
        assert len(runners) == 2
