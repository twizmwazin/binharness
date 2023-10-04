from __future__ import annotations

from pathlib import Path

from binharness import LocalEnvironment
from binharness.common.busybox import BusyboxShellExecutor
from binharness.types.executor import NullExecutor
from binharness.types.target import Target


def test_run_target() -> None:
    env = LocalEnvironment()
    target = Target(env, Path("true"))
    executor = NullExecutor()
    proc = executor.run_target(target)
    assert proc.wait() == 0


def test_run_target_busybox() -> None:
    env = LocalEnvironment()
    target = Target(env, Path("true"))
    executor = BusyboxShellExecutor()
    executor.install(env)
    assert executor.is_installed()
    proc = executor.run_target(target)
    assert proc.wait() == 0
