from __future__ import annotations

import stat
from pathlib import Path

import pytest

from binharness.localenvironment import LocalEnvironment
from binharness.types.injection import (
    ExecutableInjection,
    Injection,
    InjectionAlreadyInstalledError,
    InjectionNotInstalledError,
)


@pytest.mark.linux()
def test_inject_true() -> None:
    env = LocalEnvironment()
    true_injection = Injection(Path("/usr/bin/true"))
    true_injection.install(env)
    assert true_injection.env_path is not None
    assert stat.S_ISREG(env.stat(true_injection.env_path).mode)


@pytest.mark.linux()
def test_inject_true_executable() -> None:
    env = LocalEnvironment()
    true_injection = ExecutableInjection(Path("/usr/bin/true"))
    true_injection.install(env)
    assert true_injection.env_path is not None
    assert stat.S_ISREG(env.stat(true_injection.env_path).mode)
    assert true_injection.is_installed()
    assert env.stat(true_injection.env_path).mode & 0o111 != 0
    assert true_injection.run().wait() == 0


@pytest.mark.linux()
def test_inject_true_executable_twice() -> None:
    env = LocalEnvironment()
    true_injection = ExecutableInjection(Path("/usr/bin/true"))
    true_injection.install(env)
    with pytest.raises(InjectionAlreadyInstalledError):
        true_injection.install(env)


@pytest.mark.linux()
def test_inject_two_true_executables() -> None:
    env = LocalEnvironment()
    true_injection_1 = ExecutableInjection(Path("/usr/bin/true"))
    true_injection_1.install(env)
    true_injection_2 = ExecutableInjection(Path("/usr/bin/true"))
    true_injection_2.install(env)


def test_executable_injection_no_install() -> None:
    true_injection = ExecutableInjection(Path("/usr/bin/true"))
    with pytest.raises(InjectionNotInstalledError):
        true_injection.run()
