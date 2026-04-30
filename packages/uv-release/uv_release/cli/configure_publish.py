"""uvr configure-publish: manage publishing configuration."""

from __future__ import annotations

from diny import inject

from ..dependencies.config.uvr_publishing import UvrPublishing
from ..dependencies.configure.configure_publish_job import ConfigurePublishJob
from ..execute import execute_job


@inject
def cmd_configure_publish(publishing: UvrPublishing, job: ConfigurePublishJob) -> None:
    if not job.commands:
        print("Publishing configuration ([tool.uvr.publish]):")
        print(f"  index: {publishing.index or '(not set)'}")
        print(f"  environment: {publishing.environment or '(not set)'}")
        print(f"  trusted-publishing: {publishing.trusted_publishing}")
        print(f"  include: {', '.join(sorted(publishing.include)) or '(all)'}")
        print(f"  exclude: {', '.join(sorted(publishing.exclude)) or '(none)'}")
        return

    execute_job(job)
    print("Updated publishing configuration.")
