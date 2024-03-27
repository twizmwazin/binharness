"""binharness.localenvironment - A local environment."""

from __future__ import annotations

import fcntl
import os
import shutil
import subprocess
import tempfile
import typing
from pathlib import Path
from typing import AnyStr, Sequence

from binharness.types.environment import Environment
from binharness.types.io import IO
from binharness.types.process import Process
from binharness.types.stat import FileStat
from binharness.util import normalize_args


class LocalIO(IO[AnyStr]):
    """A file-like object for the local environment."""

    inner: typing.IO[AnyStr]

    def __init__(self: LocalIO[AnyStr], inner: typing.IO[AnyStr]) -> None:
        """Create a LocalIO."""
        self.inner = inner

    def close(self: LocalIO[AnyStr]) -> None:
        """Close the file."""
        return self.inner.close()

    @property
    def closed(self: LocalIO[AnyStr]) -> bool:
        """Whether the file is closed."""
        return self.inner.closed

    def flush(self: LocalIO[AnyStr]) -> None:
        """Flush the file."""
        return self.inner.flush()

    def read(self: LocalIO[AnyStr], n: int = -1) -> AnyStr:
        """Read n bytes from the file."""
        return self.inner.read(n)

    def readable(self: LocalIO[AnyStr]) -> bool:
        """Whether the file is readable."""
        return self.inner.readable()

    def readline(self: LocalIO[AnyStr], limit: int = -1) -> AnyStr:
        """Read a line from the file."""
        return self.inner.readline(limit)

    def readlines(self: LocalIO[AnyStr], hint: int = -1) -> list[AnyStr]:
        """Read lines from the file."""
        return self.inner.readlines(hint)

    def seek(self: LocalIO[AnyStr], offset: int, whence: int = 0) -> int | None:
        """Seek to a position in the file."""
        return self.inner.seek(offset, whence)

    def seekable(self: LocalIO[AnyStr]) -> bool:
        """Whether the file is seekable."""
        return self.inner.seekable()

    def tell(self: LocalIO[AnyStr]) -> int:
        """Get the current position in the file."""
        return self.inner.tell()

    def writable(self: LocalIO[AnyStr]) -> bool:
        """Whether the file is writable."""
        return self.inner.writable()

    def write(self: LocalIO[AnyStr], s: AnyStr) -> int | None:
        """Write to the file."""
        return self.inner.write(s)

    def writelines(self: LocalIO[AnyStr], lines: list[AnyStr]) -> None:
        """Write lines to the file."""
        self.inner.writelines(lines)

    def set_blocking(self: LocalIO[AnyStr], blocking: bool) -> None:  # noqa: FBT001
        """Set the file to non-blocking mode."""
        fd = self.inner.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        if blocking:
            flags &= ~os.O_NONBLOCK
        else:
            flags |= os.O_NONBLOCK
        fcntl.fcntl(fd, fcntl.F_SETFL, flags)


class LocalEnvironment(Environment):
    """A local environment is the environment local to where binharness is run."""

    _managed_processes: dict[int, LocalProcess]
    _metadata: dict[str, str]

    def __init__(self: LocalEnvironment) -> None:
        """Create a LocalEnvironment."""
        super().__init__()
        self._managed_processes = {}
        self._metadata = {}

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
        process = LocalProcess(self, normalize_args(*args), env=env, cwd=cwd)
        self._managed_processes[process.pid] = process
        return process

    def get_process_ids(self: LocalEnvironment) -> list[int]:
        """Get the PIDs of all processes managed by binharness in the environment."""
        return list(self._managed_processes.keys())

    def get_process(self: LocalEnvironment, pid: int) -> Process:
        """Get a process by PID."""
        return self._managed_processes[pid]

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
        return LocalIO(Path.open(path, mode))

    def chown(self: Environment, path: Path, user: str, group: str) -> None:
        """Change the owner of a file."""
        shutil.chown(path, user, group)

    def chmod(self: Environment, path: Path, mode: int) -> None:
        """Change the mode of a file."""
        path.chmod(mode)

    def stat(self: Environment, path: Path) -> FileStat:
        """Get the stat of a file."""
        return FileStat.from_os(path.stat())

    # Metadata API

    def get_metadata(self: LocalEnvironment, key: str) -> str | None:
        """Get a metadata value."""
        return self._metadata.get(key, None)

    def set_metadata(self: LocalEnvironment, key: str, value: str) -> None:
        """Set a metadata value."""
        self._metadata[key] = value


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
    def pid(self: LocalProcess) -> int:
        """Get the process' PID."""
        return self.popen.pid

    @property
    def stdin(self: LocalProcess) -> IO[bytes] | None:
        """Get the standard input stream of the process."""
        if self.popen.stdin is not None:
            return LocalIO(self.popen.stdin)
        return None

    @property
    def stdout(self: LocalProcess) -> IO[bytes] | None:
        """Get the standard output stream of the process."""
        if self.popen.stdout is not None:
            return LocalIO(self.popen.stdout)
        return None

    @property
    def stderr(self: LocalProcess) -> IO[bytes] | None:
        """Get the standard error stream of the process."""
        if self.popen.stderr is not None:
            return LocalIO(self.popen.stderr)
        return None

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
