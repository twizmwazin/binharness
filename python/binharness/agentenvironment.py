"""binharness.agentenvironment - AgentEnvironment class."""

from __future__ import annotations

import stat
from functools import cached_property
from pathlib import Path
from typing import Sequence, cast

from bh_agent_client import BhAgentClient

from binharness.types.environment import Environment
from binharness.types.io import IO
from binharness.types.process import Process
from binharness.types.stat import FileStat
from binharness.util import normalize_args


class AgentIO(IO[bytes]):
    """AgentIO implements the IO interface for agents."""

    # TODO: This doesn't do bytes/str right just yet. We need to be able to
    #  query the agent for the encoding of the file.
    _client: BhAgentClient
    _environment_id: int
    _fd: int

    def __init__(
        self: AgentIO, client: BhAgentClient, environment_id: int, fd: int
    ) -> None:
        """Create an AgentIO."""
        self._client = client
        self._environment_id = environment_id
        self._fd = fd

    def close(self: AgentIO) -> None:
        """Close the file."""
        return self._client.file_close(self._environment_id, self._fd)

    @property
    def closed(self: AgentIO) -> bool:
        """Whether the file is closed."""
        return self._client.file_is_closed(self._environment_id, self._fd)

    def flush(self: AgentIO) -> None:
        """Flush the file."""
        # TODO: Need to implement this in the agent protocol

    def read(self: AgentIO, n: int = -1) -> bytes:
        """Read n bytes from the file."""
        return self._client.file_read(
            self._environment_id, self._fd, None if n == -1 else n
        )

    def readable(self: AgentIO) -> bool:
        """Whether the file is readable."""
        return self._client.file_is_readable(self._environment_id, self._fd)

    def readline(self: AgentIO, limit: int = -1) -> bytes:  # noqa: ARG002
        """Read a line from the file."""
        lines = self._client.file_read_lines(self._environment_id, self._fd, 1)
        if lines:
            return lines[0]
        return b""  # TODO: Verify this matches python stdlib behavior

    def readlines(self: AgentIO, hint: int = -1) -> list[bytes]:
        """Read lines from the file."""
        return self._client.file_read_lines(self._environment_id, self._fd, hint)

    def seek(self: AgentIO, offset: int, whence: int = 0) -> int | None:
        """Seek to a position in the file."""
        return self._client.file_seek(self._environment_id, self._fd, offset, whence)

    def seekable(self: AgentIO) -> bool:
        """Whether the file is seekable."""
        return self._client.file_is_seekable(self._environment_id, self._fd)

    def tell(self: AgentIO) -> int:
        """Get the current position in the file."""
        return self._client.file_tell(self._environment_id, self._fd)

    def writable(self: AgentIO) -> bool:
        """Whether the file is writable."""
        return self._client.file_is_writable(self._environment_id, self._fd)

    def write(self: AgentIO, s: bytes) -> int | None:
        """Write to the file."""
        return self._client.file_write(self._environment_id, self._fd, s)

    def writelines(self: AgentIO, lines: list[bytes]) -> None:
        """Write lines to the file."""
        self._client.file_write(self._environment_id, self._fd, b"\n".join(lines))

    def set_blocking(self: AgentIO, blocking: bool) -> None:  # noqa: FBT001
        """Set the file to non-blocking mode."""
        self._client.file_set_blocking(self._environment_id, self._fd, blocking)


class AgentProcess(Process):
    """A process running in an agent environment."""

    _client: BhAgentClient
    _env_id: int
    _pid: int

    def __init__(  # noqa: PLR0913
        self: AgentProcess,
        client: BhAgentClient,
        env_id: int,
        pid: int,
        environment: Environment,
        args: Sequence[str],
        env: dict[str, str] | None,
        cwd: Path | None,
    ) -> None:
        """Create an AgentProcess."""
        super().__init__(environment, args, env, cwd)
        self._client = client
        self._env_id = env_id
        self._pid = pid

    @property
    def pid(self: AgentProcess) -> int:
        """Get the process' PID."""
        return self._pid

    @cached_property
    def stdin(self: AgentProcess) -> AgentIO | None:
        """Get the standard input stream of the process."""
        try:
            fd = self._client.get_process_channel(self._env_id, self._pid, 0)
            return AgentIO(self._client, self._env_id, fd)
        except RuntimeError:
            return None  # TODO: verify that this is the right error

    @cached_property
    def stdout(self: AgentProcess) -> AgentIO | None:
        """Get the standard output stream of the process."""
        try:
            fd = self._client.get_process_channel(self._env_id, self._pid, 1)
            return AgentIO(self._client, self._env_id, fd)
        except RuntimeError:
            return None  # TODO: verify that this is the right error

    @cached_property
    def stderr(self: AgentProcess) -> AgentIO | None:
        """Get the standard error stream of the process."""
        try:
            fd = self._client.get_process_channel(self._env_id, self._pid, 2)
            return AgentIO(self._client, self._env_id, fd)
        except RuntimeError:
            return None  # TODO: verify that this is the right error

    @property
    def returncode(self: AgentProcess) -> int | None:
        """Get the process' exit code."""
        return self._client.process_returncode(self._env_id, self._pid)

    def poll(self: AgentProcess) -> int | None:
        """Return the process' exit code if it has terminated, or None."""
        return self._client.process_poll(self._env_id, self._pid)

    def wait(self: AgentProcess, timeout: float | None = None) -> int:
        """Wait for the process to terminate and return its exit code."""
        if not self._client.process_wait(self._env_id, self._pid, timeout):
            return cast(int, self.returncode)
        raise TimeoutError


class AgentEnvironment(Environment):
    """AgentEnvironment implements the Environment interface for agents."""

    _client: BhAgentClient
    _id: int

    def __init__(self: AgentEnvironment, client: BhAgentClient, id_: int) -> None:
        """Create an AgentEnvironment."""
        self._client = client
        self._id = id_

    def run_command(
        self: AgentEnvironment,
        *args: Path | str | Sequence[Path | str],
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> AgentProcess:
        """Run a command in the environment."""
        normalized_args = list(normalize_args(*args))

        pid = self._client.run_process(
            env_id=self._id,
            argv=normalized_args,
            stdin=True,
            stdout=True,
            stderr=True,
            executable=str(normalized_args[0]),
            env=list(env.items()) if env else None,
            cwd=str(cwd) if cwd else None,
            setuid=None,
            setgid=None,
            setpgid=False,
        )
        return AgentProcess(
            self._client,
            self._id,
            pid,
            self,
            normalized_args,
            env,
            cwd,
        )

    def get_process_ids(self: AgentEnvironment) -> list[int]:
        """Get the PIDs of all processes managed by binharness in the environment."""
        return self._client.get_process_ids(self._id)

    def get_process(self: AgentEnvironment, pid: int) -> Process:
        """Get a process by PID."""
        # TODO: These last three arguments are a lie. We need to store these on
        # the agent at the time of process creation, and then retrieve them here.
        return AgentProcess(self._client, self._id, pid, self, [], None, None)

    def inject_files(self: AgentEnvironment, files: list[tuple[Path, Path]]) -> None:
        """Inject files into the environment."""
        for src, dst in files:
            # TODO: Need a more robust solution to this. Current solution fixes
            #  the common case where we're injecting into the system temp dir,
            #  which presumably already exists.
            try:
                self.stat(dst.parent)
            except RuntimeError:
                self.run_command(
                    "mkdir",  # TODO: Native mkdir function
                    "-p",
                    str(dst.parent),
                ).wait()
            try:
                dst_stat = self.stat(dst)
            except RuntimeError:
                dst_stat = None
            if dst_stat and stat.S_ISDIR(dst_stat.mode):
                adjusted_dst = dst / src.name
            else:
                adjusted_dst = dst
            fd = self._client.file_open(self._id, str(adjusted_dst), "wb")
            with src.open("rb") as f:
                while chunk := f.read(4194304):  # 4MB
                    self._client.file_write(self._id, fd, chunk)
            self._client.file_close(self._id, fd)
            local_attrs = src.stat()
            self.chmod(adjusted_dst, local_attrs.st_mode)

    def retrieve_files(self: AgentEnvironment, files: list[tuple[Path, Path]]) -> None:
        """Retrieve files from the environment."""
        for src, dst in files:
            fd = self._client.file_open(self._id, str(src), "rb")
            attrs = self.stat(src)
            with dst.open("wb") as f:
                while chunk := self._client.file_read(self._id, fd, 4096):
                    f.write(chunk)
            dst.chmod(attrs.mode)

    def get_tempdir(self: AgentEnvironment) -> Path:
        """Get a Path for a temporary directory."""
        return Path(self._client.get_tempdir(self._id))

    def open_file(self: AgentEnvironment, path: Path, mode: str) -> IO[bytes]:  # type: ignore [override]
        """Open a file in the environment. Follows the same semantics as `open`."""
        # TODO: Need to better handle mode/typing here
        fd = self._client.file_open(self._id, str(path), mode)
        return AgentIO(self._client, self._id, fd)

    def chown(self: AgentEnvironment, path: Path, user: str, group: str) -> None:
        """Change the owner of a file."""
        self._client.chown(self._id, str(path), user, group)

    def chmod(self: AgentEnvironment, path: Path, mode: int) -> None:
        """Change the mode of a file."""
        self._client.chmod(self._id, str(path), mode)

    def stat(self: AgentEnvironment, path: Path) -> FileStat:
        """Get the stat of a file."""
        return FileStat.from_agent(self._client.stat(self._id, str(path)))

    # Metadata API

    def get_metadata(self: AgentEnvironment, key: str) -> str | None:
        """Get a metadata value."""
        return self._client.get_metadata(self._id, key)

    def set_metadata(self: AgentEnvironment, key: str, value: str) -> None:
        """Set a metadata value."""
        self._client.set_metadata(self._id, key, value)


class AgentConnection:
    """AgentConnection represents a connection to an agent.

    It serves as the main interface for interacting with the agent client.
    """

    _client: BhAgentClient
    _env_cache: dict[int, AgentEnvironment]

    def __init__(self: AgentConnection, host: str, port: int) -> None:
        """Create an AgentConnection."""
        self._client = BhAgentClient.initialize_client(host, port)
        self._env_cache = {}

    def get_environment_ids(self: AgentConnection) -> list[int]:
        """Get a list of environment IDs that are currently active on the agent."""
        return self._client.get_environments()

    def get_environment(self: AgentConnection, id_: int) -> AgentEnvironment:
        """Get an AgentEnvironment for the given environment ID."""
        if id_ not in self._env_cache:
            new_env = AgentEnvironment(self._client, id_)
            self._env_cache[id_] = new_env
            return new_env
        return self._env_cache[id_]
