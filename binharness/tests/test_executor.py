from __future__ import annotations

from pathlib import Path

import pytest

from binharness.executor import (
    BusyboxShellExecutor,
    ExecutorEnvironmentMismatchError,
)
from binharness.inject import InjectionNotInstalledError
from binharness.localenvironment import LocalEnvironment
from binharness.target import Target


def test_busybox_injection_without_install() -> None:
    env = LocalEnvironment()
    target = Target(env, Path("/bin/true"))
    busybox_shell = BusyboxShellExecutor()
    with pytest.raises(InjectionNotInstalledError):
        assert busybox_shell.run_target(target)


def test_busybox_injection_different_environment() -> None:
    env1 = LocalEnvironment()
    env2 = LocalEnvironment()
    target = Target(env1, Path("/bin/true"))
    busybox_shell = BusyboxShellExecutor()
    busybox_shell.install(env2)
    with pytest.raises(ExecutorEnvironmentMismatchError):
        assert busybox_shell.run_target(target)
