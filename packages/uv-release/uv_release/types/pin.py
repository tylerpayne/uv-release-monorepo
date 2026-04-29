"""Pin: a dependency version pin."""

from .base import Frozen


class Pin(Frozen):
    """A single dependency pin: package_path and its new dep specs."""

    package_path: str
    pins: dict[str, str]
