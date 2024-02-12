from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import pytest

from binharness.bootstrap.docker import bootstrap_env_from_image
from binharness.bootstrap.subprocess import SubprocessAgent
from binharness.localenvironment import LocalEnvironment

if TYPE_CHECKING:
    from binharness.agentenvironment import AgentEnvironment
    from binharness.types.environment import Environment

try:
    import docker
except ImportError:
    docker = None


ALL = {"darwin", "linux", "win32"}


def pytest_runtest_setup(item: pytest.Item) -> None:
    # Skip tests not marked as supported on the current platform
    supported_platforms = ALL.intersection(mark.name for mark in item.iter_markers())
    plat = sys.platform
    if supported_platforms and plat not in supported_platforms:
        pytest.skip(f"cannot run on platform {plat}")

    # Skip docker tests if docker is not installed
    if "docker" in list(item.iter_markers()):
        if docker is None:
            pytest.skip("docker is not installed")
        try:
            docker.from_env()
        except docker.errors.DockerException:
            pytest.skip("docker is not running")


@pytest.fixture(scope="session")
def agent_binary_host() -> str:
    expected_path = (
        Path(__file__).parent.parent.parent / "target" / "debug" / "bh_agent_server"
    ).absolute()
    if not expected_path.exists():
        pytest.skip("agent binary not found")
    return str(expected_path)


@pytest.fixture(scope="session")
def agent_binary_linux_host_arch() -> str:
    arch = platform.machine()
    # Fixup arch for arm64
    if arch == "arm64":
        arch = "aarch64"

    expected_path = (
        Path(__file__).parent.parent.parent
        / "target"
        / f"{arch}-unknown-linux-musl"
        / "debug"
        / "bh_agent_server"
    ).absolute()
    if not expected_path.exists():
        pytest.skip("agent binary not found")
    return str(expected_path)


@pytest.fixture(scope="session")
def local_env() -> LocalEnvironment:
    return LocalEnvironment()


@pytest.fixture(scope="session")
@pytest.mark.linux()
def linux_local_env() -> LocalEnvironment:
    return LocalEnvironment()


@pytest.fixture(scope="session")
def agent_env(agent_binary_host: str) -> Generator[AgentEnvironment, None, None]:
    agent = SubprocessAgent(Path(agent_binary_host))
    yield agent.get_environment(0)
    agent.stop()


@pytest.fixture(scope="session")
@pytest.mark.docker()
def docker_client() -> docker.DockerClient:
    try:
        client = docker.from_env()
    except docker.errors.DockerException:
        pytest.skip("docker is not running")
    yield client
    client.close()


@pytest.fixture(scope="session")
def docker_env(
    docker_client: docker.APIClient, agent_binary_linux_host_arch: str
) -> Generator[AgentEnvironment, None, None]:
    agent = bootstrap_env_from_image(
        agent_binary_linux_host_arch, "ubuntu:22.04", docker_client=docker_client
    )
    yield agent.get_environment(0)
    agent.container.stop()
    agent.container.remove()


@pytest.fixture(params=["local_env", "agent_env"], scope="session")
def env(request) -> Environment:  # noqa: ANN001
    return request.getfixturevalue(request.param)  # type: ignore[no-any-return]


@pytest.fixture(params=["linux_local_env", "docker_env"], scope="session")
def linux_env(request) -> Environment:  # noqa: ANN001
    return request.getfixturevalue(request.param)  # type: ignore[no-any-return]
