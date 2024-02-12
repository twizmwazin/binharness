"""binharness.common.busybox - A busybox injection."""

from __future__ import annotations

from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, cast

from binharness.types import InjectableExecutor, Target
from binharness.types.injection import ExecutableInjection

if TYPE_CHECKING:
    from binharness.types.environment import Environment
    from binharness.types.process import Process


class BusyboxInjection(ExecutableInjection):
    """A busybox injection.

    Installs a statically linked busybox binary into an environment.
    """

    BUSYBOX_PATH = Path("/usr/bin/busybox")

    def __init__(self: BusyboxInjection) -> None:
        """Create a BusyboxInjection."""
        super().__init__(self.BUSYBOX_PATH)

    def install(self: BusyboxInjection, environment: Environment) -> None:
        """Install the injection into an environment."""
        self.env_path = environment.get_tempdir() / "busybox"
        try:
            super().install(environment)
        except OSError as ex:
            # Ignore "Text file busy" errors in CI. This is likely due to
            # multiple tests running in parallel and trying to install the
            # busybox injection at the same time.
            if "PYTEST_CURRENT_TEST" in environ and (
                "[Errno 26] Text file busy" in str(ex) or "Failure" in str(ex)
            ):
                self._environment = environment
            else:
                raise

    def mktemp(
        self: BusyboxInjection, directory: bool = False  # noqa: FBT001, FBT002
    ) -> Path:
        """Run mktemp in the environment and returns the Path created."""
        proc = self.run("mktemp", "-d") if directory else self.run("mktemp")
        stdout, _ = proc.communicate()
        # TODO: Find out how to not cast
        return Path(cast(bytes, stdout).decode().strip())

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


class BusyboxShellExecutor(BusyboxInjection, InjectableExecutor):
    """BusyboxShellExecutor is a Executor that runs the target in a busybox shell."""

    def _run_target(self: BusyboxShellExecutor, target: Target) -> Process:
        return self.run(
            "sh",
            "-c",
            f"{target.main_binary} {' '.join(target.args)}",
            env=target.env,
        )
