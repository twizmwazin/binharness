"""binharness.bootstrap.ssh - SSH bootstrap module for binharness."""
from __future__ import annotations

import paramiko

from binharness.agentenvironment import AgentConnection


def bootstrap_ssh_environment_with_client(
    agent_binary: str,
    ssh_client: paramiko.SSHClient,
    ip: str,
    port: int = 60162,
    install_path: str = "bh_agent_server",
) -> AgentConnection:
    """Bootstraps an agent running on a box over ssh.

    Currently assumes the remote box is running Linux.
    """
    # Copy the agent binary over
    sftp_client = ssh_client.open_sftp()
    sftp_client.put(agent_binary, install_path)
    sftp_client.close()

    # Make the agent binary executable
    ssh_client.exec_command(f"chmod +x {install_path}")

    # Start the agent
    _, stdout, _ = ssh_client.exec_command(f"{install_path} -d {ip} {port}")

    # Create the agent connection
    return AgentConnection(ip, port)


def bootstrap_ssh_environment(
    agent_binary: str,
    ip: str,
    port: int = 60162,
    username: str = "root",
) -> AgentConnection:
    """Bootstraps an agent running on a box over ssh.

    Currently assumes the remote box is running Linux. If you need more control
    over the ssh connection, use bootstrap_ssh_environment_with_client to set up
    the ssh connection yourself.
    """
    # Create the ssh client
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect to the remote box
    ssh_client.connect(ip, username=username)

    # Bootstrap the environment
    return bootstrap_ssh_environment_with_client(agent_binary, ssh_client, ip, port)
