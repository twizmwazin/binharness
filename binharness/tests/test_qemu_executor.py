from __future__ import annotations

from pathlib import Path

from binharness import LocalEnvironment, Target
from binharness.qemu import QemuExecutor


def test_run_true() -> None:
    env = LocalEnvironment()
    target = Target(env, Path("/bin/true"))
    qemu = QemuExecutor("x86_64")
    qemu.install(env)
    assert qemu.run_target(target).wait() == 0


def test_run_strace() -> None:
    env = LocalEnvironment()
    target = Target(env, Path("/bin/true"))
    qemu = QemuExecutor("x86_64")
    qemu.install(env)
    proc, log_generator = qemu.run_with_strace(str(target.main_binary))
    assert proc.wait() == 0
    log_list = list(log_generator)
    assert len(log_list) > 0
