"""binharness.busybox - A busybox injection."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from binharness.inject import ExecutableInjection

if TYPE_CHECKING:
    from binharness.environment import Environment
    from binharness.process import Process


class BusyboxInjection(ExecutableInjection):
    """A busybox injection.

    Installs a statically linked busybox binary into an environment.
    """

    BUSYBOX_PATH = Path("/usr/bin/busybox")

    def __init__(self: BusyboxInjection) -> None:
        """Create a BusyboxInjection."""
        super().__init__(Path("busybox"), self.BUSYBOX_PATH, None)

    def install(self: BusyboxInjection, environment: Environment) -> None:
        """Install the injection into an environment."""
        self.env_path = environment.get_tempdir()
        super().install(environment)
        environment.busybox_injection = self

    def mktemp(
        self: BusyboxInjection, directory: bool = False  # noqa: FBT001, FBT002
    ) -> Path:
        """Run mktemp in the environment and returns the Path created."""
        proc = self.run("mktemp", "-d") if directory else self.run("mktemp")
        stdout, _ = proc.communicate()
        return Path(stdout.decode().strip())

    def shell(
        self: BusyboxInjection, command: str, env: dict[str, str] | None = None
    ) -> Process:
        """Run a shell in the environment."""
        return self.run("sh", "-c", command, env=env)

    def cat(self: BusyboxInjection, path: Path) -> Process:
        """Run cat in the environment."""
        return self.run("cat", str(path))

    def nc(
        self: BusyboxInjection,
        host: str,
        port: int,
        listen: bool = False,  # noqa: FBT001, FBT002
    ) -> Process:
        """Run nc in the environment."""
        if listen:
            return self.run("nc", "-lp", str(port))
        return self.run("nc", host, str(port))
