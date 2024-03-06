"""binharness.bootstrap.subprocess - Agent bootstrap using a subprocess."""

from __future__ import annotations

import os
import subprocess
import time
from typing import TYPE_CHECKING

from binharness.agentenvironment import AgentConnection

if TYPE_CHECKING:
    from pathlib import Path


class SubprocessAgent(AgentConnection):
    """SubprocessAgent runs an agent as a subprocess.

    It provides the same interface as a standard AgentConnection, but adds
    functions for managing the lifecycle of the agent.
    """

    _process: subprocess.Popen

    def __init__(
        self: SubprocessAgent,
        agent_binary: Path,
        address: str = "127.0.0.1",
        port: int = 60162,
    ) -> None:
        """Create an AgentConnection."""
        process = subprocess.Popen(
            [str(agent_binary), address, str(port)],
            env={**os.environ, "RUST_LOG": "bh_agent_server::util::read_chars=trace"},
        )
        self._process = process
        time.sleep(0.1)
        super().__init__(address, port)

    def stop(self: SubprocessAgent) -> None:
        """Shutdown the agent."""
        self._process.terminate()
        self._process.wait()
