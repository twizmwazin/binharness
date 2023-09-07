"""binharness.inject - Inject files into an environment."""
from __future__ import annotations

from typing import TYPE_CHECKING

from binharness.environment import BusyboxInjectionNotInstalledError

if TYPE_CHECKING:
    from pathlib import Path

    from binharness import Environment, Process


class InjectionError(Exception):
    """An error occurred while injecting a file into an environment."""


class InjectionNotInstalledError(InjectionError):
    """An injection is not installed and associated with an environment."""


class InjectionAlreadyInstalledError(InjectionError):
    """An injection is already installed and associated with an environment."""


class Injection:
    """A file injection.

    An injection is a file that is injected into an environment.
    """

    host_path: Path
    env_path: Path | None

    _environment: Environment | None

    def __init__(
        self: Injection, host_path: Path, env_path: Path | None = None
    ) -> None:
        """Create an Injection."""
        self.host_path = host_path
        self.env_path = env_path
        self._environment = None

    def install(self: Injection, environment: Environment) -> None:
        """Install the injection into an environment."""
        if self._environment is not None:
            raise InjectionAlreadyInstalledError
        if self.env_path is None:
            try:
                bb_injection = environment.busybox_injection
            except BusyboxInjectionNotInstalledError:
                from binharness.busybox import BusyboxInjection

                bb_injection = BusyboxInjection()
                bb_injection.install(environment)
            self.env_path = bb_injection.mktemp(directory=True)

        environment.inject_files([(self.host_path, self.env_path)])
        self._environment = environment

    def is_installed(self: Injection) -> bool:
        """Return True if the injection is installed."""
        return self._environment is not None

    @property
    def environment(self: Injection) -> Environment:
        """Return the environment the injection is installed in."""
        if self._environment is None:
            raise InjectionNotInstalledError
        return self._environment


class ExecutableInjection(Injection):
    """An executable file injection.

    An executable injection is a file that is injected into an environment and
    made executable. Once installed, ExecutableInjections are bound to an
    environment.
    """

    executable: Path

    def __init__(
        self: ExecutableInjection,
        executable: Path,
        host_path: Path,
        env_path: Path | None = None,
    ) -> None:
        """Create an ExecutableInjection."""
        super().__init__(host_path, env_path)
        self.executable = executable

    def run(
        self: ExecutableInjection,
        *args: str,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> Process:
        """Run the injection in the environment."""
        if self._environment is None or self.env_path is None:
            raise InjectionNotInstalledError
        return self._environment.run_command(
            [self.env_path / self.executable, *args],
            env=env,
            cwd=cwd,
        )
