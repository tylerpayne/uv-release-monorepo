"""Tests for runner propagation in multi-runner monorepos.

Uses the _compute_effective_runners function directly with a topology
modeled after a real monorepo with mixed platform requirements.
"""

from __future__ import annotations

from uv_release.dependencies.build.build_job import _compute_effective_runners
from uv_release.dependencies.build.build_packages import BuildPackages
from uv_release.dependencies.config.uvr_runners import UvrRunners
from uv_release.types.package import Package
from uv_release.types.version import Version

_V = Version.parse("0.1.0.dev0")

# Simplified monorepo topology:
#
#   quicksand-core         (linux)          no deps
#   quicksand-smb          (linux)          no deps
#   quicksand-build-tools  (linux)          no deps
#   quicksand-qemu         (windows, linux, macos, linux-arm64)  build-dep: build-tools
#   quicksand-image-tools  (linux)          dep: core
#   quicksand-ubuntu       (linux, macos)   build-deps: image-tools, core, qemu, smb
#   quicksand-alpine       (linux, macos)   build-deps: image-tools, core, qemu, smb
#   quicksand-agent        (linux, macos)   dep: core, ubuntu; build-deps: image-tools, core, ubuntu, qemu, smb
#   quicksand-cua          (linux, macos)   dep: core, agent; build-deps: image-tools, core, agent, ubuntu, qemu, smb

LINUX = ["self-hosted", "linux", "x64"]
MACOS = ["self-hosted", "macos", "arm64"]
WINDOWS = ["self-hosted", "x64", "windows"]
LINUX_ARM = ["self-hosted", "linux", "arm64"]

PACKAGES: dict[str, Package] = {
    "quicksand-core": Package(
        name="quicksand-core",
        path="packages/quicksand-core",
        version=_V,
        dependencies=[],
        build_dependencies=[],
    ),
    "quicksand-smb": Package(
        name="quicksand-smb",
        path="packages/quicksand-smb",
        version=_V,
        dependencies=[],
        build_dependencies=[],
    ),
    "quicksand-build-tools": Package(
        name="quicksand-build-tools",
        path="packages/quicksand-build-tools",
        version=_V,
        dependencies=[],
        build_dependencies=[],
    ),
    "quicksand-qemu": Package(
        name="quicksand-qemu",
        path="packages/quicksand-qemu",
        version=_V,
        dependencies=[],
        build_dependencies=["quicksand-build-tools"],
    ),
    "quicksand-image-tools": Package(
        name="quicksand-image-tools",
        path="packages/quicksand-image-tools",
        version=_V,
        dependencies=["quicksand-core"],
        build_dependencies=[],
    ),
    "quicksand-ubuntu": Package(
        name="quicksand-ubuntu",
        path="packages/quicksand-ubuntu",
        version=_V,
        dependencies=["quicksand-core"],
        build_dependencies=[
            "quicksand-image-tools",
            "quicksand-core",
            "quicksand-qemu",
            "quicksand-smb",
        ],
    ),
    "quicksand-alpine": Package(
        name="quicksand-alpine",
        path="packages/quicksand-alpine",
        version=_V,
        dependencies=["quicksand-core"],
        build_dependencies=[
            "quicksand-image-tools",
            "quicksand-core",
            "quicksand-qemu",
            "quicksand-smb",
        ],
    ),
    "quicksand-agent": Package(
        name="quicksand-agent",
        path="packages/quicksand-agent",
        version=_V,
        dependencies=["quicksand-core", "quicksand-ubuntu"],
        build_dependencies=[
            "quicksand-image-tools",
            "quicksand-core",
            "quicksand-ubuntu",
            "quicksand-qemu",
            "quicksand-smb",
        ],
    ),
    "quicksand-cua": Package(
        name="quicksand-cua",
        path="packages/quicksand-cua",
        version=_V,
        dependencies=["quicksand-core", "quicksand-agent"],
        build_dependencies=[
            "quicksand-image-tools",
            "quicksand-core",
            "quicksand-agent",
            "quicksand-ubuntu",
            "quicksand-qemu",
            "quicksand-smb",
        ],
    ),
}

RUNNERS = UvrRunners(
    items={
        "quicksand-core": [LINUX],
        "quicksand-smb": [LINUX],
        "quicksand-build-tools": [LINUX],
        "quicksand-qemu": [WINDOWS, LINUX, MACOS, LINUX_ARM],
        "quicksand-image-tools": [LINUX],
        "quicksand-ubuntu": [LINUX, MACOS],
        "quicksand-alpine": [LINUX, MACOS],
        "quicksand-agent": [LINUX, MACOS],
        "quicksand-cua": [LINUX, MACOS],
    }
)

BUILD_PACKAGES = BuildPackages(items=PACKAGES)


class TestMonorepoRunnerPropagation:
    """Verify runner propagation with a realistic multi-platform monorepo."""

    def _effective(self) -> dict[str, list[list[str]]]:
        return _compute_effective_runners(PACKAGES, RUNNERS, BUILD_PACKAGES)

    def test_alpine_does_not_run_on_windows(self) -> None:
        """quicksand-alpine should NOT build on the Windows runner."""
        eff = self._effective()
        alpine_runners = eff.get("quicksand-alpine", [])
        assert WINDOWS not in alpine_runners

    def test_alpine_runs_on_linux_and_macos(self) -> None:
        """quicksand-alpine is configured for linux and macos."""
        eff = self._effective()
        alpine_runners = eff.get("quicksand-alpine", [])
        assert LINUX in alpine_runners
        assert MACOS in alpine_runners

    def test_qemu_runs_on_all_four(self) -> None:
        """quicksand-qemu has its own 4 runners."""
        eff = self._effective()
        qemu_runners = eff.get("quicksand-qemu", [])
        assert WINDOWS in qemu_runners
        assert LINUX in qemu_runners
        assert MACOS in qemu_runners
        assert LINUX_ARM in qemu_runners

    def test_build_tools_inherits_from_qemu(self) -> None:
        """quicksand-build-tools is a build dep of qemu, inherits qemu's runners."""
        eff = self._effective()
        bt_runners = eff.get("quicksand-build-tools", [])
        assert WINDOWS in bt_runners
        assert LINUX in bt_runners
        assert MACOS in bt_runners

    def test_smb_inherits_from_all_dependents(self) -> None:
        """quicksand-smb is a build dep of ubuntu, alpine, agent, cua."""
        eff = self._effective()
        smb_runners = eff.get("quicksand-smb", [])
        assert LINUX in smb_runners
        assert MACOS in smb_runners

    def test_smb_does_not_inherit_windows(self) -> None:
        """No package that depends on smb runs on windows, so smb shouldn't either."""
        eff = self._effective()
        smb_runners = eff.get("quicksand-smb", [])
        assert WINDOWS not in smb_runners

    def test_core_inherits_from_all_dependents(self) -> None:
        """quicksand-core is depended on by almost everything."""
        eff = self._effective()
        core_runners = eff.get("quicksand-core", [])
        assert LINUX in core_runners
        assert MACOS in core_runners

    def test_cua_only_on_own_runners(self) -> None:
        """quicksand-cua should only run on its own linux and macos."""
        eff = self._effective()
        cua_runners = eff.get("quicksand-cua", [])
        assert WINDOWS not in cua_runners
        assert LINUX_ARM not in cua_runners
        assert len(cua_runners) == 2
