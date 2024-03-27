"""binharness.types.process - A process running in an environment."""

from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from pathlib import Path

    from binharness.types.environment import Environment
    from binharness.types.io import IO


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
    def pid(self: Process) -> int:
        """Get the process' PID."""
        raise NotImplementedError

    @abstractproperty
    def stdin(self: Process) -> IO[bytes] | None:
        """Get the standard input stream of the process."""
        raise NotImplementedError

    @abstractproperty
    def stdout(self: Process) -> IO[bytes] | None:
        """Get the standard output stream of the process."""
        raise NotImplementedError

    @abstractproperty
    def stderr(self: Process) -> IO[bytes] | None:
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
    def wait(self: Process, timeout: float | None = None) -> int:
        """Wait for the process to terminate and return its exit code."""
        raise NotImplementedError

    def communicate(
        self: Process, input_: bytes | None = None, timeout: float | None = None
    ) -> tuple[bytes | None, bytes | None]:
        """Send input to the process and return its output and error streams."""
        if self.stdin is not None:
            if input_ is not None:
                self.stdin.write(input_)
            self.stdin.close()
        self.wait(timeout)
        stdout = self.stdout.read() if self.stdout is not None else None
        stderr = self.stderr.read() if self.stderr is not None else None
        return (stdout, stderr)
