from __future__ import annotations

from pathlib import Path

import pytest

from binharness import Environment, Target
from binharness.common.qemu import QemuExecutor


@pytest.mark.linux
def test_run_true(env: Environment) -> None:
    target = Target(env, Path("/bin/true"))
    qemu = QemuExecutor()
    qemu.install(env)
    assert qemu.run_target(target).wait() == 0


@pytest.mark.linux
def test_run_strace(env: Environment) -> None:
    target = Target(env, Path("/bin/true"))
    qemu = QemuExecutor()
    qemu.install(env)
    proc, log_generator = qemu.run_with_strace(str(target.main_binary))
    assert proc.wait() == 0
    log_list = list(log_generator)
    assert len(log_list) > 0
