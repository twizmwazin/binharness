"""binharness.environment - Base Environment class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from binharness import BusyboxInjection, Process


class Envirnoment(ABC):
    """An environment is a place where a target can run.

    An environment provides the base API for creating and invoking targets.
    Environment provides low level APIs for file injection and retrieval, as
    well as running commands.
    """

    busybox_injection: BusyboxInjection | None

    def __init__(self: Envirnoment) -> None:
        """Create an Environment."""
        self.busybox_injection = None

    @abstractmethod
    def run_command(
        self: Envirnoment,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> Process:
        """Run a command in the environment.

        The command is run as a process in the environment. For now, arguments
        are passed to Process as-is.
        """
        raise NotImplementedError

    @abstractmethod
    def inject_files(
        self: Envirnoment,
        files: list[tuple[Path, Path]],
    ) -> None:
        """Inject files into the environment.

        The first element of the tuple is the path to the file on the host
        machine, the second element is the path to the file in the environment.
        """
        raise NotImplementedError

    @abstractmethod
    def retrieve_files(
        self: Envirnoment,
        files: list[tuple[Path, Path]],
    ) -> None:
        """Retrieve files from the environment.

        The first element of the tuple is the path to the file in the
        environment, the second element is the path to the file on the host
        machine.
        """
        raise NotImplementedError

    @abstractmethod
    def get_tempdir(self: Envirnoment) -> Path:
        """Get a Path for a temporary directory."""
        raise NotImplementedError
