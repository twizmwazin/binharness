"""binharness.common.qemu - QEMU injection."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import TYPE_CHECKING, Generator, cast

from binharness.types.executor import InjectableExecutor
from binharness.types.injection import ExecutableInjection
from binharness.types.io import IO
from binharness.util import generate_random_suffix, read_lines

if TYPE_CHECKING:
    from binharness import Process, Target


def _get_qemu_host_arch() -> str:
    """Get the host architecture."""
    return platform.machine()  # TODO: Does this work on all platforms?


class QemuInjection(ExecutableInjection):
    """A QEMU injection.

    Installs a statically linked QEMU binary into an environment.
    """

    arch: str

    def __init__(self: QemuInjection, arch: str | None = None) -> None:
        """Create a QemuInjection."""
        self.arch = arch if arch is not None else _get_qemu_host_arch()
        super().__init__(Path(f"/usr/bin/qemu-{self.arch}-static"))

    def run_with_log(
        self: QemuInjection,
        *args: str,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> tuple[Process, Generator[bytes, None, None]]:
        """Run the injection in the environment and return a log generator."""
        logfile = (
            self.environment.get_tempdir() / f"qemu-{generate_random_suffix()}.log"
        )
        proc = self.run(
            "-D",
            str(logfile),
            *args,
            env=env,
            cwd=cwd,
        )

        def log_generator() -> Generator[bytes, None, None]:
            file = self.environment.open_file(logfile, "rb")
            yield from read_lines(cast(IO[bytes], file))

            # Cleanup log file
            self.environment.run_command("rm", logfile)

        return proc, log_generator()

    def run_with_strace(
        self: QemuInjection,
        *args: str,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> tuple[Process, Generator[bytes, None, None]]:
        """Run the injection in the environment and return a strace log generator."""
        return self.run_with_log(
            "-strace",
            *args,
            env=env,
            cwd=cwd,
        )


class QemuExecutor(QemuInjection, InjectableExecutor):
    """A QEMU executor.

    Provides the Executor API on top of QemuInjection.
    """

    def _run_target(self: QemuExecutor, target: Target) -> Process:
        """Run a target in an environment."""
        return self.run(
            str(target.main_binary),
            *target.args,
            env=target.env,
        )
