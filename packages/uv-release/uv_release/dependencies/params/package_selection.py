"""PackageSelection: which packages the user requested."""

from diny import singleton

from ...types.base import Frozen


@singleton
class PackageSelection(Frozen):
    """Seeded by CLI. Controls which packages are targeted."""

    all_packages: bool = False
    packages: frozenset[str] = frozenset()
    exclude_packages: frozenset[str] = frozenset()
