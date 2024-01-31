from __future__ import annotations

import pathlib
import tempfile
from typing import TYPE_CHECKING

import pytest

from binharness.common.busybox import BusyboxInjection

if TYPE_CHECKING:
    from binharness import Environment


def test_run_command(env: Environment) -> None:
    proc = env.run_command(["echo", "hello"])
    stdout, _ = proc.communicate()
    assert proc.returncode == 0
    assert stdout == b"hello\n"


def test_inject_files(env: Environment) -> None:
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


# TODO: Need to think about how to handle this test with remote environments
def test_get_tempdir(local_env: Environment) -> None:
    assert local_env.get_tempdir() == pathlib.Path(tempfile.gettempdir())


# TODO: Need to think about how to test these with non-linux environments
@pytest.mark.linux()
def test_stdout(env: Environment) -> None:
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.shell("echo hello")
    assert proc.stdout is not None
    assert proc.stdout.read() == b"hello\n"


@pytest.mark.linux()
def test_stderr(env: Environment) -> None:
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.shell("echo hello 1>&2")
    assert proc.stderr is not None
    assert proc.stderr.read() == b"hello\n"


@pytest.mark.linux()
def test_process_poll(env: Environment) -> None:
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.run("head")
    assert proc.poll() is None
    assert proc.stdin is not None
    proc.stdin.write(b"hello\n")
    proc.stdin.close()
    proc.wait()
    assert proc.poll() is not None
    assert proc.stdout is not None
    assert proc.stdout.read() == b"hello\n"
