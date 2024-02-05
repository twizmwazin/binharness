"""binharness.bootstrap.ssh - SSH bootstrap module for binharness."""

from __future__ import annotations

import time

import paramiko

from binharness.agentenvironment import AgentConnection


class SSHAgent(AgentConnection):
    """SSHAgent implements the AgentConnection interface for agents over SSH.

    It provides the same interface as a standard AgentConnection, but adds
    functions for managing the lifecycle of the agent.
    """

    _ssh_client: paramiko.SSHClient

    def __init__(
        self: SSHAgent, ssh_client: paramiko.SSHClient, host: str, port: int
    ) -> None:
        """Create an AgentConnection."""
        super().__init__(host, port)
        self._ssh_client = ssh_client

    def stop(self: SSHAgent) -> None:
        """Shutdown the agent."""
        self._ssh_client.exec_command("kill $(cat /tmp/bh_agent_server.pid)")


def bootstrap_ssh_environment_with_client(  # noqa: PLR0913
    agent_binary: str,
    ssh_client: paramiko.SSHClient,
    connect_ip: str,
    listen_ip: str = "0.0.0.0",  # noqa: S104
    listen_port: int = 60162,
    connect_port: int = 60162,
    install_path: str = "bh_agent_server",
) -> SSHAgent:
    """Bootstraps an agent running on a box over ssh.

    Currently assumes the remote box is running Linux or macOS. A reference to
    the ssh client is held to allow management of the agent process. If the
    client is closed, the management functions will no longer work.
    """
    # Copy the agent binary over
    sftp_client = ssh_client.open_sftp()
    sftp_client.put(agent_binary, install_path)
    sftp_client.close()

    # Make the agent binary executable
    ssh_client.exec_command(f"chmod +x {install_path}")

    # Start the agent
    ssh_client.exec_command(f"{install_path} -d {listen_ip} {listen_port}")

    # Wait for the agent to start
    time.sleep(1)

    # Create the agent connection
    return SSHAgent(ssh_client, connect_ip, connect_port)


def bootstrap_ssh_environment(
    agent_binary: str,
    ip: str,
    port: int = 60162,
    username: str = "root",
) -> SSHAgent:
    """Bootstraps an agent running on a box over ssh.

    Currently assumes the remote box is running Linux. If you need more control
    over the ssh connection, use bootstrap_ssh_environment_with_client to set up
    the ssh connection yourself.
    """
    # Create the ssh client
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # noqa: S507

    # Connect to the remote box
    ssh_client.connect(ip, username=username)

    # Bootstrap the environment
    return bootstrap_ssh_environment_with_client(
        agent_binary, ssh_client, ip, listen_port=port, connect_port=port
    )
