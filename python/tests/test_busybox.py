from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from binharness.common.busybox import BusyboxInjection

if TYPE_CHECKING:
    from binharness import Environment


@pytest.mark.linux()
def test_busybox_injection(env: Environment) -> None:
    busybox_injection = BusyboxInjection()
    busybox_injection.install(env)
    assert busybox_injection.run("true").wait() == 0
    assert busybox_injection.run("false").wait() == 1

    proc = busybox_injection.run(
        "head",
        "-n",
        "1",
    )
    assert proc.stdin is not None
    stdout, _ = proc.communicate(b"one\ntwo\n")
    assert proc.returncode == 0
    assert stdout == b"one\n"


@pytest.mark.linux()
def test_busbox_injection_mktemp(env: Environment) -> None:
    busybox_injection = BusyboxInjection()
    busybox_injection.install(env)
    assert busybox_injection.mktemp().is_file()
    assert busybox_injection.mktemp(directory=True).is_dir()


# TODO: Make this work on agents, probably an issue in wait()
@pytest.mark.linux()
def test_nc_interaction(local_env: Environment) -> None:
    busybox = BusyboxInjection()
    busybox.install(local_env)

    server_proc = busybox.nc("localhost", 10001, listen=True)
    client_proc = busybox.nc("localhost", 10001)

    assert client_proc.stdin is not None
    assert server_proc.stdin is not None
    client_proc.stdin.write(b"hello\n")
    client_proc.stdin.flush()
    server_proc.stdin.write(b"hello back\n")
    server_proc.stdin.flush()

    assert server_proc.stdout is not None
    assert server_proc.stdout.readline() == b"hello\n"
    assert client_proc.stdout is not None
    assert client_proc.stdout.readline() == b"hello back\n"

    client_proc.stdin.close()
    client_proc.wait()
    server_proc.stdin.close()
    server_proc.wait()
