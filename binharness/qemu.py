"""binharness.qemu - QEMU injection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Generator

from binharness.executor import InjectableExecutor
from binharness.inject import ExecutableInjection
from binharness.util import read_lines

if TYPE_CHECKING:
    from binharness import Process, Target


class QemuInjection(ExecutableInjection):
    """A QEMU injection.

    Installs a statically linked QEMU binary into an environment.
    """

    arch: str

    def __init__(self: QemuInjection, arch: str) -> None:
        """Create a QemuInjection."""
        self.arch = arch
        super().__init__(
            Path(f"qemu-{arch}-static"), Path(f"/usr/bin/qemu-{arch}-static")
        )

    def run_with_log(
        self: QemuInjection,
        *args: str,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> tuple[Process, Generator[bytes, None, None]]:
        """Run the injection in the environment and return a log generator."""
        logfile = self.environment.busybox_injection.mktemp()
        proc = self.run(
            "-D",
            str(logfile),
            *args,
            env=env,
            cwd=cwd,
        )

        def log_generator() -> Generator[bytes, None, None]:
            cat_proc = self.environment.busybox_injection.cat(logfile)
            yield from read_lines(cat_proc.stdout)

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
