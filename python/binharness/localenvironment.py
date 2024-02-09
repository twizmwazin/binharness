"""binharness.localenvironment - A local environment."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, AnyStr, Sequence

from binharness.types.environment import Environment
from binharness.types.process import Process
from binharness.types.stat import FileStat
from binharness.util import normalize_args

if TYPE_CHECKING:
    from binharness.types.io import IO


class LocalEnvironment(Environment):
    """A local environment is the environment local to where binharness is run."""

    def __init__(self: LocalEnvironment) -> None:
        """Create a LocalEnvironment."""
        super().__init__()

    def run_command(
        self: LocalEnvironment,
        *args: Path | str | Sequence[Path | str],
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> Process:
        """Run a command in the environment.

        The command is run in a subprocess and the subprocess is returned. The
        subprocess is started with `subprocess.Popen` and the arguments are
        passed directly to that function.
        """
        return LocalProcess(self, normalize_args(*args), env=env, cwd=cwd)

    def inject_files(
        self: LocalEnvironment,
        files: list[tuple[Path, Path]],
    ) -> None:
        """Inject files into the environment.

        The first element of the tuple is the path to the file on the host
        machine, the second element is the path to the file in the environment.
        """
        for file in files:
            file[1].parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file[0], file[1])

    def retrieve_files(
        self: LocalEnvironment,
        files: list[tuple[Path, Path]],
    ) -> None:
        """Retrieve files from the environment.

        The first element of the tuple is the path to the file in the
        environment, the second element is the path to the file on the host
        machine.
        """
        for file in files:
            shutil.copy(file[0], file[1])

    def get_tempdir(self: LocalEnvironment) -> Path:
        """Get a Path for a temporary directory."""
        return Path(tempfile.gettempdir())

    def open_file(self: Environment, path: Path, mode: str) -> IO[AnyStr]:
        """Open a file in the environment. Follows the same semantics as `open`."""
        return Path.open(path, mode)

    def chown(self: Environment, path: Path, user: str, group: str) -> None:
        """Change the owner of a file."""
        shutil.chown(path, user, group)

    def chmod(self: Environment, path: Path, mode: int) -> None:
        """Change the mode of a file."""
        path.chmod(mode)

    def stat(self: Environment, path: Path) -> FileStat:
        """Get the stat of a file."""
        return FileStat.from_os(path.stat())


class LocalProcess(Process):
    """A process running in a local environment."""

    popen: subprocess.Popen[bytes]

    def __init__(
        self: LocalProcess,
        environment: Environment,
        args: Sequence[str],
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> None:
        """Create a LocalProcess."""
        super().__init__(environment, args, env=env, cwd=cwd)
        self.popen = subprocess.Popen(
            self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=cwd,
            universal_newlines=False,
        )

    @property
    def stdin(self: LocalProcess) -> IO[bytes] | None:
        """Get the standard input stream of the process."""
        return self.popen.stdin

    @property
    def stdout(self: LocalProcess) -> IO[bytes] | None:
        """Get the standard output stream of the process."""
        return self.popen.stdout

    @property
    def stderr(self: LocalProcess) -> IO[bytes] | None:
        """Get the standard error stream of the process."""
        return self.popen.stderr

    @property
    def returncode(self: LocalProcess) -> int | None:
        """Get the process' exit code."""
        return self.popen.returncode

    def poll(self: LocalProcess) -> int | None:
        """Return the process' exit code if it has terminated, or None."""
        return self.popen.poll()

    def wait(self: LocalProcess, timeout: float | None = None) -> int:
        """Wait for the process to terminate and return its exit code."""
        return self.popen.wait(timeout=timeout)
