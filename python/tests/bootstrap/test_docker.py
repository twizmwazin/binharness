from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from binharness.bootstrap.docker import DockerAgent, bootstrap_env_from_image
from binharness.types.executor import NullExecutor
from binharness.types.target import Target

if TYPE_CHECKING:
    import docker


def test_bootstrap_env_from_image(
    docker_client: docker.APIClient, agent_binary_linux_host_arch: str
) -> None:
    agent = bootstrap_env_from_image(
        agent_binary_linux_host_arch, "ubuntu:22.04", docker_client=docker_client
    )
    try:
        assert isinstance(agent, DockerAgent)
        assert agent.get_environment_ids() == [0]

        env = agent.get_environment(0)
        target = Target(env, Path("/usr/bin/echo"), args=["hello world"])
        proc = NullExecutor().run_target(target)

        proc.wait()
        assert proc.returncode == 0
        assert proc.stdout is not None
        assert proc.stdout.read() == b"hello world\n"
    finally:
        agent.container.kill()
