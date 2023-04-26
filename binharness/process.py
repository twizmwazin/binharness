"""binharness.process - A process running in an environment."""
from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from typing import TYPE_CHECKING, AnyStr, Protocol, Sequence

if TYPE_CHECKING:
    from pathlib import Path

    from binharness.environment import Environment


class IO(Protocol[AnyStr]):
    """A file-like object."""

    def close(self: IO) -> None:
        """Close the file."""

    @property
    def closed(self: IO) -> bool:
        """Whether the file is closed."""

    def flush(self: IO) -> None:
        """Flush the file."""

    def read(self: IO, n: int = -1) -> AnyStr:
        """Read n bytes from the file."""

    def readable(self: IO) -> bool:
        """Whether the file is readable."""

    def readline(self: IO, limit: int = -1) -> AnyStr:
        """Read a line from the file."""

    def readlines(self: IO, hint: int = -1) -> list[AnyStr]:
        """Read lines from the file."""

    def seek(self: IO, offset: int, whence: int = 0) -> int | None:
        """Seek to a position in the file."""

    def seekable(self: IO) -> bool:
        """Whether the file is seekable."""

    def tell(self: IO) -> int:
        """Get the current position in the file."""

    def writable(self: IO) -> bool:
        """Whether the file is writable."""

    def write(self: IO, s: AnyStr) -> int | None:
        """Write to the file."""

    def writelines(self: IO, lines: list[AnyStr]) -> None:
        """Write lines to the file."""


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
    def wait(self: Process, timeout: float | None = None) -> int:
        """Wait for the process to terminate and return its exit code."""
        raise NotImplementedError

    def communicate(
        self: Process, input_: bytes | None = None, timeout: float | None = None
    ) -> tuple[bytes, bytes]:
        """Send input to the process and return its output and error streams."""
        if input_ is not None:
            self.stdin.write(input_)
        self.stdin.close()
        self.wait(timeout)
        return (self.stdout.read(), self.stderr.read())
