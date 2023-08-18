"""binharness.sshenvironment: SSHEnvironment."""
from __future__ import annotations

import shlex
import stat
from pathlib import Path
from typing import Any, Sequence

import paramiko

from binharness.environment import Environment
from binharness.process import IO, Process
from binharness.util import join_normalized_args, normalize_args


class SSHEnvironmentError(Exception):
    """An error occurred in an SSHEnvironment."""


class SSHInvalidArgumentsError(SSHEnvironmentError):
    """Invalid arguments were passed to an SSHEnvironment."""


class SSHNotConnectedError(SSHEnvironmentError):
    """An SSHEnvironment is not connected to a host."""


class SSHPermissionError(SSHEnvironmentError):
    """An SSHEnvironment does not have permission to perform an action."""


class SSHProcess(Process):
    """A process running in an SSHEnvironment."""

    _channel: paramiko.Channel
    _returncode: int | None

    def __init__(  # noqa: PLR0913
        self: SSHProcess,
        channel: paramiko.Channel,
        environment: SSHEnvironment,
        args: Sequence[str],
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> None:
        """Create a Process."""
        super().__init__(environment, args, env=env, cwd=cwd)
        self._channel = channel
        self._returncode = None
        self._channel.update_environment(
            {key.encode(): value.encode() for key, value in self.env.items()}
        )
        command_str = join_normalized_args(self.args)
        command_str = "cd " + shlex.quote(str(self.cwd)) + " && " + command_str
        self._channel.exec_command(command_str)

    @property
    def stdin(self: SSHProcess) -> IO[bytes]:
        """Get the standard input stream of the process."""
        return self._channel.makefile_stdin("wb")

    @property
    def stdout(self: SSHProcess) -> IO[bytes]:
        """Get the standard output stream of the process."""
        return self._channel.makefile("rb")

    @property
    def stderr(self: SSHProcess) -> IO[bytes]:
        """Get the standard error stream of the process."""
        return self._channel.makefile_stderr("rb")

    @property
    def returncode(self: SSHProcess) -> int | None:
        """Get the process' exit code."""
        return self._returncode

    def poll(self: SSHProcess) -> int | None:
        """Return the process' exit code if it has terminated, or None."""
        rc = (
            self._channel.recv_exit_status()
            if self._channel.exit_status_ready()
            else None
        )
        if rc is not None:
            self._returncode = rc
        return rc

    def wait(self: SSHProcess, timeout: float | None = None) -> int:
        """Wait for the process to terminate and return its exit code."""
        if timeout is not None:
            self._channel.settimeout(timeout)
        while True:
            rc = self._channel.recv_exit_status()
            if rc is not None:
                self._returncode = rc
                break
        return self._channel.recv_exit_status()


class SSHEnvironment(Environment):
    """An environment over SSH."""

    _client: paramiko.SSHClient
    _tmp_base: Path

    def __init__(
        self: SSHEnvironment,
        *,
        client: paramiko.SSHClient | None = None,
        hostname: str | None = None,
        connection_args: dict[str, Any] | None = None,
        tmp_base: Path = Path("/tmp"),
    ) -> None:
        """Create a SSHEnvironment."""
        super().__init__()
        if (client is None and hostname is None) or (
            client is not None and hostname is not None
        ):
            raise SSHInvalidArgumentsError
        if client is not None:
            self._client = client
        if hostname is not None:
            self._connect(hostname, connection_args if connection_args else {})
        self._tmp_base = tmp_base

    # API Methods

    def run_command(
        self: SSHEnvironment,
        *args: Path | str | Sequence[Path | str],
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> SSHProcess:
        """Run a command in the environment.

        The command is run as a process in the environment. For now, arguments
        are passed to Process as-is.
        """
        transport = self._client.get_transport()
        if transport is None:
            raise SSHNotConnectedError
        return SSHProcess(
            transport.open_session(), self, normalize_args(*args), env=env, cwd=cwd
        )

    def inject_files(
        self: SSHEnvironment,
        files: list[tuple[Path, Path]],
    ) -> None:
        """Inject files into the environment.

        The first element of the tuple is the path to the file on the host
        machine, the second element is the path to the file in the environment.
        """
        sftp = self._client.open_sftp()
        for file in files:
            dest_path = file[1]
            if _is_dir(sftp, dest_path):
                dest_path = dest_path / file[0].name
            else:
                _make_dirs(sftp, dest_path.parent)
            sftp.put(str(file[0]), str(dest_path))
            sftp.chmod(str(dest_path), stat.S_IMODE(file[0].stat().st_mode))
        sftp.close()

    def retrieve_files(
        self: SSHEnvironment,
        files: list[tuple[Path, Path]],
    ) -> None:
        """Retrieve files from the environment.

        The first element of the tuple is the path to the file in the
        environment, the second element is the path to the file on the host
        machine.
        """
        sftp = self._client.open_sftp()
        for file in files:
            sftp.get(str(file[0]), str(file[1]))
        sftp.close()

    def get_tempdir(self: SSHEnvironment) -> Path:
        """Get a Path for a temporary directory."""
        return self._tmp_base

    # Connection Methods
    def _connect(
        self: SSHEnvironment, host: str, connection_args: dict[str, Any]
    ) -> None:  # pragma: no cover
        """Connect to the environment."""
        self._client = paramiko.SSHClient()
        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(host, **connection_args)

    def close(self: SSHEnvironment) -> None:
        """Close the connection to the environment."""
        if hasattr(self, "_client"):
            self._client.close()

    def __del__(self: SSHEnvironment) -> None:
        """Close the connection to the environment."""
        self.close()


# Utility functions for SFTP


def _is_dir(sftp: paramiko.SFTPClient, path: Path) -> bool:
    try:
        file_mode = sftp.stat(str(path)).st_mode
    except FileNotFoundError:
        return False
    if file_mode is None:
        raise SSHEnvironmentError
    return bool(stat.S_ISDIR(file_mode))


def _make_dirs(sftp: paramiko.SFTPClient, path: Path) -> None:
    working_path = path
    while len(path.parts) > 1:
        try:
            sftp.mkdir(str(working_path))
        except PermissionError as err:  # noqa: PERF203
            # No permission to create directory
            raise SSHPermissionError from err
        except FileNotFoundError:  # Parent directory does not exist
            _make_dirs(sftp, working_path.parent)
        except OSError:  # Directory already exists
            return
