from __future__ import annotations

import pathlib
import tempfile
from typing import TYPE_CHECKING, Generator

import mockssh
import pytest

from binharness.common.busybox import BusyboxInjection
from binharness.environment.sshenvironment import (
    SSHEnvironment,
    SSHInvalidArgumentsError,
    SSHNotConnectedError,
    _is_dir,
    _make_dirs,
)

if TYPE_CHECKING:
    import paramiko


USER_KEYS = {
    "test": str((pathlib.Path(__file__).parent / "ssh_keys" / "test").absolute()),
}


@pytest.fixture()
def ssh_server() -> Generator[mockssh.Server, None, None]:
    with mockssh.Server(USER_KEYS) as server:
        yield server


@pytest.fixture()
def ssh_client(ssh_server: mockssh.Server) -> Generator[paramiko.SSHClient, None, None]:
    client = ssh_server.client("test")
    yield client
    client.close()


@pytest.fixture()
def sftp_client(
    ssh_client: paramiko.SSHClient,
) -> Generator[paramiko.SFTPClient, None, None]:
    sftp_client = ssh_client.open_sftp()
    yield sftp_client
    sftp_client.close()


@pytest.fixture()
def env(ssh_server: mockssh.Server) -> Generator[SSHEnvironment, None, None]:
    env = SSHEnvironment(client=ssh_server.client("test"))
    yield env
    env.close()


@pytest.fixture()
def busybox(env: SSHEnvironment) -> BusyboxInjection:
    busybox = BusyboxInjection()
    busybox.install(env)
    return busybox


def test_run_command(env: SSHEnvironment) -> None:
    proc = env.run_command(["echo", "hello"])
    stdout, _ = proc.communicate(timeout=5)
    assert proc.returncode == 0
    assert stdout == b"hello\n"


def test_inject_files(env: SSHEnvironment) -> None:
    env_temp = env.get_tempdir()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        file = tmp_path / "test.txt"
        file.write_text("hello")
        env.inject_files([(file, env_temp / "test.txt")])

    with tempfile.TemporaryDirectory() as tmp_dir:
        local_file = pathlib.Path(tmp_dir) / "test.txt"
        env.retrieve_files([(env_temp / "test.txt", local_file)])
        assert local_file.read_text() == "hello"


def test_get_tempdir(env: SSHEnvironment) -> None:
    assert env.get_tempdir() == pathlib.Path("/tmp")


def test_stdout(env: SSHEnvironment) -> None:
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.shell("echo hello")
    assert proc.stdout.read() == b"hello\n"


def test_stderr(env: SSHEnvironment) -> None:
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.shell("echo hello 1>&2")
    assert proc.stderr.read() == b"hello\n"


def test_process_poll(env: SSHEnvironment) -> None:
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.run("sleep", "0.1")
    assert proc.poll() is None
    proc.wait()
    assert proc.poll() is not None


def test_invalid_args() -> None:
    with pytest.raises(SSHInvalidArgumentsError):
        SSHEnvironment()


def test_command_after_close(env: SSHEnvironment) -> None:
    env.close()
    with pytest.raises(SSHNotConnectedError):
        env.run_command(["echo", "hello"])


def test_connect_hostname(ssh_server: mockssh.Server) -> None:
    SSHEnvironment(
        hostname=ssh_server.host,
        connection_args={
            "port": ssh_server.port,
            "username": "test",
            "key_filename": USER_KEYS["test"],
            "allow_agent": False,
            "look_for_keys": False,
        },
    ).close()


def test_is_dir(sftp_client: paramiko.SFTPClient) -> None:
    assert _is_dir(sftp_client, pathlib.Path("/tmp"))


def test_make_dir(sftp_client: paramiko.SFTPClient) -> None:
    _make_dirs(sftp_client, pathlib.Path("/tmp/test"))


def test_make_dir_already_exists(sftp_client: paramiko.SFTPClient) -> None:
    _make_dirs(sftp_client, pathlib.Path("/"))
