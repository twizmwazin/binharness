from __future__ import annotations

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
    true_injection = Injection(Path("/usr/bin/true"), None)
    true_injection.install(env)
    assert true_injection.env_path is not None
    assert true_injection.env_path.is_file()


@pytest.mark.linux()
def test_inject_true_executable() -> None:
    env = LocalEnvironment()
    true_injection = ExecutableInjection(Path("true"), Path("/usr/bin/true"))
    true_injection.install(env)
    assert true_injection.env_path is not None
    assert true_injection.env_path.is_file()
    assert true_injection.is_installed()
    assert true_injection.env_path.stat().st_mode & 0o111 != 0
    assert true_injection.run().wait() == 0


@pytest.mark.linux()
def test_inject_true_executable_twice() -> None:
    env = LocalEnvironment()
    true_injection = ExecutableInjection(Path("true"), Path("/usr/bin/true"))
    true_injection.install(env)
    with pytest.raises(InjectionAlreadyInstalledError):
        true_injection.install(env)


@pytest.mark.linux()
def test_inject_two_true_executables() -> None:
    env = LocalEnvironment()
    true_injection_1 = ExecutableInjection(Path("true"), Path("/usr/bin/true"))
    true_injection_1.install(env)
    true_injection_2 = ExecutableInjection(Path("true"), Path("/usr/bin/true"))
    true_injection_2.install(env)


def test_executable_injection_no_install() -> None:
    true_injection = ExecutableInjection(Path("true"), Path("/usr/bin/true"))
    with pytest.raises(InjectionNotInstalledError):
        true_injection.run()
