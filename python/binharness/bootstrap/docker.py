"""binharness.bootstrap.docker - Docker bootstrap for binharness."""
from __future__ import annotations

import io
import tarfile
from typing import BinaryIO

import docker

from binharness.agentenvironment import AgentConnection


class DockerAgent(AgentConnection):
    """DockerAgent implements the AgentConnection interface for Docker.

    It provides the same interface as a standard AgentConnection, but
    it allows managing the agent in a docker container.
    """

    _client: docker.DockerClient
    _container_id: str

    def __init__(self: DockerAgent, container_id: str, port: int) -> None:
        """Initialize a DockerAgent."""
        self._client = docker.from_env()
        self._container_id = container_id

        container = self._client.containers.get(container_id)
        ip_address = container.attrs["NetworkSettings"]["IPAddress"]
        super().__init__(ip_address, port)

    def __del__(self: DockerAgent) -> None:
        """__del__ is overridden to ensure that the docker client is closed."""
        self._client.close()


def _create_in_memory_tarfile(files: dict[str, str]) -> BinaryIO:
    file_like_object = io.BytesIO()

    with tarfile.open(fileobj=file_like_object, mode="w") as tar:
        for src, dst in files.items():
            tar.add(src, arcname=dst)

    file_like_object.seek(0)
    return file_like_object


def bootstrap_env_from_image(
    agent_binary: str, image: str, port: int = 60162
) -> DockerAgent:
    """Bootstraps an agent running in a docker container."""
    client = docker.from_env()
    try:
        # Setup container
        client.images.pull(image)
        container = client.containers.create(
            image,
            command=["/agent", "0.0.0.0", str(port)],  # noqa: S104
        )
        # Transfer agent binary to container
        archive = _create_in_memory_tarfile({agent_binary: "agent"})
        container.put_archive("/", archive)
        # Start agent
        container.start()
        # Get IP address of container
        container.reload()
        # Build agent
        return DockerAgent(container.id, port)
    finally:
        client.close()
