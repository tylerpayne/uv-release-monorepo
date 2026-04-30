"""uvr configure: manage workspace configuration."""

from __future__ import annotations

from diny import inject

from ..dependencies.config.uvr_config import UvrConfig
from ..dependencies.configure.configure_job import ConfigureJob
from ..execute import execute_job


@inject
def cmd_configure(config: UvrConfig, job: ConfigureJob) -> None:
    if not job.commands:
        print("Configuration ([tool.uvr.config]):")
        print(f"  latest: {config.latest_package or '(not set)'}")
        print(f"  python_version: {config.python_version}")
        print(f"  include: {', '.join(sorted(config.include)) or '(all)'}")
        print(f"  exclude: {', '.join(sorted(config.exclude)) or '(none)'}")
        return

    execute_job(job)
    print("Updated configuration.")
