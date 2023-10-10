"""binharness.types.environment - Base Environment class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AnyStr, Sequence

if TYPE_CHECKING:
    from pathlib import Path

    from binharness import IO, BusyboxInjection, Process


class BusyboxInjectionNotInstalledError(Exception):
    """BusyBox is not installed in the environment."""


class Environment(ABC):
    """An environment is a place where a target can run.

    An environment provides the base API for creating and invoking targets.
    Environment provides low level APIs for file injection and retrieval, as
    well as running commands.
    """

    _busybox_injection: BusyboxInjection | None

    def __init__(self: Environment) -> None:
        """Create an Environment."""
        self._busybox_injection = None

    @property
    def busybox_injection(self: Environment) -> BusyboxInjection:
        """Return the BusyboxInjection for the environment."""
        if self._busybox_injection is None:
            raise BusyboxInjectionNotInstalledError
        return self._busybox_injection

    @busybox_injection.setter
    def busybox_injection(
        self: Environment,
        busybox_injection: BusyboxInjection,
    ) -> None:
        """Set the BusyboxInjection for the environment."""
        self._busybox_injection = busybox_injection

    @abstractmethod
    def run_command(
        self: Environment,
        *args: Path | str | Sequence[Path | str],
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> Process:
        """Run a command in the environment.

        The command is run as a process in the environment. For now, arguments
        are passed to Process as-is.
        """
        raise NotImplementedError

    @abstractmethod
    def inject_files(
        self: Environment,
        files: list[tuple[Path, Path]],
    ) -> None:
        """Inject files into the environment.

        The first element of the tuple is the path to the file on the host
        machine, the second element is the path to the file in the environment.
        """
        raise NotImplementedError

    @abstractmethod
    def retrieve_files(
        self: Environment,
        files: list[tuple[Path, Path]],
    ) -> None:
        """Retrieve files from the environment.

        The first element of the tuple is the path to the file in the
        environment, the second element is the path to the file on the host
        machine.
        """
        raise NotImplementedError

    @abstractmethod
    def get_tempdir(self: Environment) -> Path:
        """Get a Path for a temporary directory."""
        raise NotImplementedError

    @abstractmethod
    def open_file(self: Environment, path: Path, mode: str) -> IO[AnyStr]:
        """Open a file in the environment. Follows the same semantics as `open`."""
        raise NotImplementedError
