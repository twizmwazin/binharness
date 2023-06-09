"""binharness.executor - A way to run a target in an environment."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from binharness.inject import (
    BusyboxInjection,
    Injection,
    InjectionNotInstalledError,
)

if TYPE_CHECKING:
    from binharness import Process, Target


class ExecutorError(Exception):
    """An error occurred while running a target in an Executor."""


class ExecutorEnvironmentMismatchError(ExecutorError):
    """The Executor and target environments do not match."""


class Executor(ABC):
    """A Executor is a way to run a target in an environment."""

    @abstractmethod
    def run_target(self: Executor, target: Target) -> Process:
        """Run a target in its environment."""
        raise NotImplementedError


class InjectableExecutor(Executor, Injection):
    """InjectableExecutor is a Executor that must be injected into an environment."""

    @abstractmethod
    def _run_target(self: InjectableExecutor, target: Target) -> Process:
        """Run a target in an environment."""
        raise NotImplementedError

    def run_target(self: InjectableExecutor, target: Target) -> Process:
        """Run a target in its environment."""
        if not self.is_installed():
            raise InjectionNotInstalledError
        if self._environment != target.environment:
            raise ExecutorEnvironmentMismatchError
        return self._run_target(target)


class NullExecutor(Executor):
    """NullExecutor is a Executor that just runs the target as a command."""

    def run_target(self: NullExecutor, target: Target) -> Process:
        """Run a target in an environment without any wrappers."""
        return target.environment.run_command(
            target.main_binary,
            *target.args,
            env=target.env,
        )


class BusyboxShellExecutor(BusyboxInjection, InjectableExecutor):
    """BusyboxShellExecutor is a Executor that runs the target in a busybox shell."""

    def _run_target(self: BusyboxShellExecutor, target: Target) -> Process:
        return self.run(
            "sh",
            "-c",
            f"{target.main_binary} {' '.join(target.args)}",
            env=target.env,
        )
