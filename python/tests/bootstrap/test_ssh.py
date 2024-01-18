from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Generator

import mockssh
import pytest

from binharness.agentenvironment import AgentConnection
from binharness.bootstrap.ssh import bootstrap_ssh_environment_with_client
from binharness.types.executor import NullExecutor
from binharness.types.target import Target

if TYPE_CHECKING:
    from paramiko import SSHClient

SAMPLE_USER_KEY = str(Path(mockssh.__file__).parent / "sample-user-key")


@pytest.fixture()
def ssh_server() -> Generator[mockssh.Server, None, None]:
    users = {"test": SAMPLE_USER_KEY}
    with mockssh.Server(users) as s:
        yield s


@pytest.fixture()
def ssh_client(ssh_server: mockssh.Server) -> SSHClient:
    return ssh_server.client(0)  # type: ignore[no-any-return]


def test_bootstrap_ssh_environment_with_client(
    ssh_server: mockssh.Server, agent_binary_host: str
) -> None:
    agent = bootstrap_ssh_environment_with_client(
        agent_binary_host,
        ssh_server.client("test"),
        "127.0.0.1",
        install_path="/tmp/bh_agent_server",
    )

    try:
        assert isinstance(agent, AgentConnection)
        assert agent.get_environment_ids() == [0]

        env = agent.get_environment(0)
        target = Target(env, Path("/usr/bin/echo"), args=["hello world"])
        proc = NullExecutor().run_target(target)

        proc.wait()
        assert proc.returncode == 0
        assert proc.stdout.read() == b"hello world\n"
    finally:
        agent.stop()
