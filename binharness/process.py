"""binharness.process - A process running in an environment."""
from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from typing import IO, TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from pathlib import Path

    from binharness.environment import Environment


class Process(ABC):
    """A process running in an environment."""

    environment: Environment
    args: Sequence[str]
    env: dict[str, str]
    cwd: Path

    def __init__(
        self: Process,
        environment: Environment,
        args: Sequence[str],
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> None:
        """Create a Process."""
        self.environment = environment
        self.args = args
        self.env = env or {}
        self.cwd = cwd or environment.get_tempdir()

    @abstractproperty
    def stdin(self: Process) -> IO[bytes]:
        """Get the standard input stream of the process."""
        raise NotImplementedError

    @abstractproperty
    def stdout(self: Process) -> IO[bytes]:
        """Get the standard output stream of the process."""
        raise NotImplementedError

    @abstractproperty
    def stderr(self: Process) -> IO[bytes]:
        """Get the standard error stream of the process."""
        raise NotImplementedError

    @abstractproperty
    def returncode(self: Process) -> int | None:
        """Get the process' exit code."""
        raise NotImplementedError

    @abstractmethod
    def poll(self: Process) -> int | None:
        """Return the process' exit code if it has terminated, or None."""
        raise NotImplementedError

    @abstractmethod
    def wait(self: Process) -> int:
        """Wait for the process to terminate and return its exit code."""
        raise NotImplementedError

    @abstractmethod
    def communicate(self: Process, input_: bytes | None = None) -> tuple[bytes, bytes]:
        """Send input to the process and return its output and error streams."""
        raise NotImplementedError

    @abstractmethod
    def send_signal(self: Process, signal: int) -> None:
        """Send a signal to the process."""
        raise NotImplementedError

    @abstractmethod
    def terminate(self: Process) -> None:
        """Terminate the process."""
        raise NotImplementedError

    @abstractmethod
    def kill(self: Process) -> None:
        """Kill the process."""
        raise NotImplementedError
