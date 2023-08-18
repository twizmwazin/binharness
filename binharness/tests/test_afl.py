from __future__ import annotations

from pathlib import Path

from binharness.aflexecutor import AFLExecutor
from binharness.localenvironment import LocalEnvironment
from binharness.sshenvironment import SSHEnvironment
from binharness.target import Target


def example() -> None:
    local_env = LocalEnvironment()
    SSHEnvironment("ssh_hostname")
    afl_executor = AFLExecutor(Path("/tmp/afl-seeds"))
    afl_executor.install(local_env)

    target = Target(local_env, Path("/usr/bin/busybox"), args=["sh"])

    afl_proc = afl_executor.run_target(target)

    afl_proc.wait()


if __name__ == "__main__":
    example()
