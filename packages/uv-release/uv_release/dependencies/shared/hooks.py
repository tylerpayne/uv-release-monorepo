"""Hooks: lifecycle callbacks for the release pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from diny import singleton, provider


@singleton
class Hooks:
    """Lifecycle hooks. Override by registering a custom @provider(Hooks).

    Default implementation is a no-op for every hook. Users customize by
    providing their own Hooks subclass via diny's provider mechanism.

    Per-job hooks (pre_build, post_build, etc.) are called by the executor
    via getattr, so any method named pre_{job_name} or post_{job_name} will
    be invoked at the right time.
    """

    def pre_plan(self, root: Path, command: str) -> None:
        pass

    def post_plan(self, root: Path, command: str, plan: Any) -> Any:
        return plan

    def pre_command(self, job_name: str, command: Any) -> None:
        pass

    def post_command(self, job_name: str, command: Any, returncode: int) -> None:
        pass

    def pre_build(self) -> None:
        pass

    def post_build(self) -> None:
        pass

    def pre_release(self) -> None:
        pass

    def post_release(self) -> None:
        pass

    def pre_publish(self) -> None:
        pass

    def post_publish(self) -> None:
        pass

    def pre_bump(self) -> None:
        pass

    def post_bump(self) -> None:
        pass


@provider(Hooks)
def provide_hooks() -> Hooks:
    return Hooks()
