"""ConfigureRunnersJob: mutate [tool.uvr.runners] in pyproject.toml."""

from __future__ import annotations

from diny import singleton, provider

from ...commands import WriteUvrSectionCommand
from ...types.job import Job
from ..config.uvr_runners import UvrRunners
from ..params.configure_params import ConfigureRunnersParams


@singleton
class ConfigureRunnersJob(Job):
    """Write updated runners section. Empty = show mode."""


@provider(ConfigureRunnersJob)
def provide_configure_runners_job(
    runners: UvrRunners,
    params: ConfigureRunnersParams,
) -> ConfigureRunnersJob:
    has_mutations = params.add or params.remove or params.clear

    if not has_mutations:
        return ConfigureRunnersJob(name="configure-runners")

    matrix = {k: list(v) for k, v in runners.items.items()}

    if params.clear:
        if params.package:
            matrix.pop(params.package, None)
        else:
            matrix.clear()
    else:
        if not params.package:
            raise ValueError("Specify --package when adding or removing runners.")

        pkg_runners = list(matrix.get(params.package, []))

        # Strip brackets so '[self-hosted, linux]' parses like 'self-hosted, linux'.
        for spec in params.add:
            stripped = spec.strip().strip("[]")
            labels = [label.strip() for label in stripped.split(",")]
            if labels not in pkg_runners:
                pkg_runners.append(labels)

        for spec in params.remove:
            stripped = spec.strip().strip("[]")
            labels = [label.strip() for label in stripped.split(",")]
            if labels in pkg_runners:
                pkg_runners.remove(labels)

        if pkg_runners:
            matrix[params.package] = pkg_runners
        else:
            matrix.pop(params.package, None)

    return ConfigureRunnersJob(
        name="configure-runners",
        commands=[
            WriteUvrSectionCommand(
                label="Update [tool.uvr.runners]", section="runners", data=matrix
            )
        ],
    )  # type: ignore[arg-type]
