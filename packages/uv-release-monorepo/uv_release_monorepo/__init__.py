"""uv-release-monorepo: lazy monorepo wheel builder — only rebuilds what changed."""

from importlib.metadata import version as _pkg_version

from .shared.hooks import ReleaseHook
from .shared.models import ReleasePlan

__version__ = _pkg_version("uv-release-monorepo")
__all__ = ["ReleaseHook", "ReleasePlan", "__version__"]
