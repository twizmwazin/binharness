from __future__ import annotations

from pathlib import Path

import pytest

from binharness import Environment, NullExecutor, Target
from binharness.common.busybox import BusyboxShellExecutor


def test_run_target(env: Environment) -> None:
    target = Target(env, Path("true"))
    executor = NullExecutor()
    proc = executor.run_target(target)
    assert proc.wait() == 0


@pytest.mark.linux
def test_run_target_busybox(env: Environment) -> None:
    target = Target(env, Path("true"))
    executor = BusyboxShellExecutor()
    executor.install(env)
    assert executor.is_installed()
    proc = executor.run_target(target)
    assert proc.wait() == 0
