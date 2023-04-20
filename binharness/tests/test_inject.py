from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from binharness.inject import (
    BusyboxInjection,
    ExecutableInjection,
    Injection,
    InjectionAlreadyInstalledError,
    InjectionNotInstalledError,
)
from binharness.localenvironment import LocalEnvironment


def test_inject_true() -> None:
    env = LocalEnvironment()
    true_injection = Injection(Path("/bin/true"), None)
    true_injection.install(env)
    assert true_injection.env_path is not None
    assert (true_injection.env_path / "true").is_file()


def test_inject_true_executable() -> None:
    env = LocalEnvironment()
    true_injection = ExecutableInjection(Path("true"), Path("/bin/true"))
    true_injection.install(env)
    assert true_injection.env_path is not None
    assert true_injection.env_path.is_dir()
    assert (true_injection.env_path / "true").is_file()
    assert true_injection.is_installed()
    assert true_injection.env_path.stat().st_mode & 0o111 != 0
    assert true_injection.run().wait() == 0


def test_inject_true_executable_twice() -> None:
    env = LocalEnvironment()
    true_injection = ExecutableInjection(Path("true"), Path("/bin/true"))
    true_injection.install(env)
    with pytest.raises(InjectionAlreadyInstalledError):
        true_injection.install(env)


def test_inject_two_true_executables() -> None:
    env = LocalEnvironment()
    true_injection_1 = ExecutableInjection(Path("true"), Path("/bin/true"))
    true_injection_1.install(env)
    true_injection_2 = ExecutableInjection(Path("true"), Path("/bin/true"))
    true_injection_2.install(env)


def test_executable_injection_no_install() -> None:
    true_injection = ExecutableInjection(Path("true"), Path("/bin/true"))
    with pytest.raises(InjectionNotInstalledError):
        true_injection.run()


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
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
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
