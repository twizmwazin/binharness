from __future__ import annotations

import pathlib
import signal
import tempfile

from binharness.inject import BusyboxInjection
from binharness.localenvironment import LocalEnvironment


def test_run_command() -> None:
    env = LocalEnvironment()
    proc = env.run_command(["echo", "hello"])
    stdout, _ = proc.communicate()
    assert proc.returncode == 0
    assert stdout == b"hello\n"


def test_inject_files() -> None:
    env = LocalEnvironment()
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


def test_get_tempdir() -> None:
    env = LocalEnvironment()
    assert env.get_tempdir() == pathlib.Path(tempfile.gettempdir())


def test_stdout() -> None:
    env = LocalEnvironment()
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.shell("echo hello")
    assert proc.stdout.read() == b"hello\n"


def test_stderr() -> None:
    env = LocalEnvironment()
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.shell("echo hello 1>&2")
    assert proc.stderr.read() == b"hello\n"


def test_process_poll() -> None:
    env = LocalEnvironment()
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.run("yes")
    assert proc.poll() is None
    proc.terminate()
    proc.wait()
    assert proc.poll() is not None


def test_process_send_signal() -> None:
    env = LocalEnvironment()
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.run("yes")
    proc.send_signal(signal.SIGTERM)
    proc.wait()
    assert proc.poll() == -signal.SIGTERM


def test_process_kill() -> None:
    env = LocalEnvironment()
    busybox = BusyboxInjection()
    busybox.install(env)
    proc = busybox.run("yes")
    proc.kill()
    assert proc.wait() == -signal.SIGKILL
