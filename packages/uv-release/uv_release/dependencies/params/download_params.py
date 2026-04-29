"""DownloadParams: parameters for the download subcommand."""

from diny import singleton

from ...types.base import Frozen


@singleton
class DownloadParams(Frozen):
    """Seeded by CLI. Which package/tag/run to download from."""

    package: str = ""
    release_tag: str = ""
    run_id: str = ""
    output: str = "dist"
    repo: str = ""
    all_platforms: bool = False
