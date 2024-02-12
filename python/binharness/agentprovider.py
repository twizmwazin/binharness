"""binharness.agentprovider - AgentProvider class."""

from __future__ import annotations

import abc
from pathlib import Path


class AgentProvider(abc.ABC):
    """AgentProvider class."""

    @abc.abstractmethod
    def get_agent_bin(self: AgentProvider, target_triplet: str | None = None) -> Path:
        """Return a path to the agent binary for the given target triplet.

        If target_triplet is None, return the default agent binary.
        """
        raise NotImplementedError


class DevEnvironmentAgentProvider(AgentProvider):
    """DevEnvironmentAgentProvider class."""

    path: Path
    target: str

    def __init__(
        self: DevEnvironmentAgentProvider,
        path: Path | None = None,
        target: str = "debug",
    ) -> None:
        """Initialize a DevEnvironmentAgentProvider.

        If path is not provided, the path will be set assuming the project is installed
        in development mode.
        """
        if path is None:
            self.path = Path(__file__).parent.parent.parent
        else:
            self.path = path
        self.target = target

    def get_agent_bin(
        self: DevEnvironmentAgentProvider, target_triplet: str | None = None
    ) -> Path:
        """Return a path to the agent binary for the given target triplet."""
        if target_triplet is None:
            return self.path / "target" / self.target / "bh_agent_server"
        return self.path / "target" / target_triplet / self.target / "bh_agent_server"
