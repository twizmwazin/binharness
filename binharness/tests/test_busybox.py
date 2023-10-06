from __future__ import annotations

from binharness.common.busybox import BusyboxInjection
from binharness.localenvironment import LocalEnvironment


def test_busybox_injection() -> None:
    env = LocalEnvironment()
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


def test_busbox_injection_mktemp() -> None:
    env = LocalEnvironment()
    busybox_injection = BusyboxInjection()
    busybox_injection.install(env)
    assert busybox_injection.mktemp().is_file()
    assert busybox_injection.mktemp(directory=True).is_dir()


def test_nc_interaction() -> None:
    env = LocalEnvironment()
    busybox = BusyboxInjection()
    busybox.install(env)

    server_proc = busybox.nc("localhost", 10001, listen=True)
    client_proc = busybox.nc("localhost", 10001)

    client_proc.stdin.write(b"hello\n")
    client_proc.stdin.flush()
    server_proc.stdin.write(b"hello back\n")
    server_proc.stdin.flush()

    assert server_proc.stdout.readline() == b"hello\n"
    assert client_proc.stdout.readline() == b"hello back\n"
