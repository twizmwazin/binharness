from __future__ import annotations

from pathlib import Path

import pytest

from binharness import (
    Environment,
    ExecutorEnvironmentMismatchError,
    InjectionNotInstalledError,
    LocalEnvironment,
    Target,
)
from binharness.common.busybox import BusyboxShellExecutor


@pytest.mark.linux()
def test_busybox_injection_without_install(env: Environment) -> None:
    target = Target(env, Path("/usr/bin/true"))
    busybox_shell = BusyboxShellExecutor()
    with pytest.raises(InjectionNotInstalledError):
        assert busybox_shell.run_target(target)


# TODO: Maybe LocalEnvironment objects should be interchangable?
@pytest.mark.linux()
def test_busybox_injection_different_environment() -> None:
    env1 = LocalEnvironment()
    env2 = LocalEnvironment()
    target = Target(env1, Path("/usr/bin/true"))
    busybox_shell = BusyboxShellExecutor()
    busybox_shell.install(env2)
    with pytest.raises(ExecutorEnvironmentMismatchError):
        assert busybox_shell.run_target(target)
